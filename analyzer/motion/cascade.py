"""Cascade: copies of an object arranged by a layout.

- chain: each copy is the previous one moved, rotated and scaled by one step. The
  steps compound, so small rotations give spirals and scale < 1 gives a tunnel
- phyllotaxis: sunflower spiral (golden angle), optionally rising into a cone
- grid: columns x rows x layers
- curve: copies spread along a curve, facing its direction
Sound stretches the steps per copy - with the "delay" spread a wave travels
down the chain."""
import colorsys
import math

import numpy as np
from mathutils import Euler, Matrix, Vector, geometry

from . import fields, instances, layer
from .audio import apply_cc_mods
from .lib import clamp01, elements, scene_time

MIN_SCALE = 1e-4
GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))


def _rotation(settings, factor, v, mods):
    return Euler([a * factor * (1 + settings.audio_rotation * v) * mods["twist"] for a in settings.rotation],
                 'XYZ').to_matrix().to_4x4()


def _scale_power(settings, i):
    return Matrix.Diagonal((*(s ** i for s in settings.scale_step), 1.0))


def step_matrix(settings, v, mods):
    loc = Vector(settings.offset) * (1 + settings.audio_offset * v) * mods["spread"]
    return Matrix.Translation(loc) @ _rotation(settings, 1, v, mods) @ _scale_power(settings, 1)


def curve_polyline(curve_obj, resolution=24):
    """World-space points along the first spline of a curve object."""
    if curve_obj is None or curve_obj.type != 'CURVE' or not curve_obj.data.splines:
        return None, False
    spline = curve_obj.data.splines[0]
    pts = []
    if spline.type == 'BEZIER':
        bp = list(spline.bezier_points)
        pairs = list(zip(bp, bp[1:])) + ([(bp[-1], bp[0])] if spline.use_cyclic_u and len(bp) > 1 else [])
        for a, b in pairs:
            seg = geometry.interpolate_bezier(a.co, a.handle_right, b.handle_left, b.co, resolution)
            pts.extend(seg if not pts else seg[1:])
        if not pairs:
            pts = [p.co for p in bp]
    else:
        pts = [p.co.xyz for p in spline.points]
    m = curve_obj.matrix_world
    return [m @ Vector(p) for p in pts], spline.use_cyclic_u


def sample_polyline(pts, fraction, cyclic):
    """Position and tangent at fraction (0..1) of the polyline length."""
    if len(pts) == 1:
        return pts[0], Vector((0, 1, 0))
    seg = [(b - a).length for a, b in zip(pts, pts[1:])]
    total = sum(seg) or 1.0
    fraction = fraction % 1.0 if cyclic else clamp01(fraction)
    target = fraction * total
    for i, length in enumerate(seg):
        if target <= length or i == len(seg) - 1:
            t = target / length if length else 0
            a, b = pts[i], pts[i + 1]
            tangent = (b - a).normalized() if length else Vector((0, 1, 0))
            return a.lerp(b, min(max(t, 0), 1)), tangent
        target -= length


def matrices(base, settings, values, mods=None):
    """World matrices for copies 1..len(values); copy 0 is the source itself."""
    mods = mods or {"reveal": settings.reveal, "spread": 1.0, "twist": 1.0}
    count = len(values)
    reveal = clamp01(mods["reveal"] + settings.audio_reveal * (values[0] if values else 0))
    layout = settings.layout
    polyline, cyclic = curve_polyline(settings.curve_object) if layout == 'curve' else (None, False)
    out = []
    m = base.copy()
    loc, rot, scale = base.decompose()
    for idx, v in enumerate(values):
        i = idx + 1
        stretch = (1 + settings.audio_offset * v) * mods["spread"]
        if layout == 'chain':
            m = m @ step_matrix(settings, v, mods)
            element = m
        elif layout == 'phyllotaxis':
            theta = i * GOLDEN_ANGLE
            r = settings.spacing * math.sqrt(i) * stretch
            pos = Vector((r * math.cos(theta), r * math.sin(theta), settings.offset[2] * i * stretch))
            element = base @ Matrix.Translation(pos) @ Matrix.Rotation(theta, 4, 'Z') \
                      @ _rotation(settings, i, v, mods) @ _scale_power(settings, i)
        elif layout == 'grid':
            cols, rows = max(1, settings.grid_columns), max(1, settings.grid_rows)
            cell = Vector((i % cols, (i // cols) % rows, i // (cols * rows)))
            element = base @ Matrix.Translation(cell * settings.spacing * stretch) \
                      @ _rotation(settings, i, v, mods) @ _scale_power(settings, i)
        else:  # curve
            if polyline is None:
                return []
            along = idx / count if cyclic else idx / max(1, count - 1)
            pos, tangent = sample_polyline(polyline, settings.curve_offset + along * stretch, cyclic)
            element = Matrix.Translation(pos) @ tangent.to_track_quat('Y', 'Z').to_matrix().to_4x4() \
                      @ _rotation(settings, i, v, mods) @ Matrix.Diagonal((*scale, 1.0)) @ _scale_power(settings, i)
        pulse = max(MIN_SCALE, 1 + settings.audio_scale * v)
        visible = max(MIN_SCALE, clamp01(reveal * count - idx))
        out.append(element @ Matrix.Scale(pulse * visible, 4))
    return out


def colors(settings, values, t):
    out = []
    for i, v in enumerate(values):
        hue = (settings.hue + settings.hue_step * (i + 1) + settings.hue_speed * t + settings.audio_hue * v) % 1.0
        out.append((*colorsys.hsv_to_rgb(hue, settings.saturation, 1.0), 1.0))
    return out


def update(engine, obj, scene, frame):
    settings = obj.audvis.cascade
    instanced = settings.output == 'instances' and settings.instancer is not None
    copies = None if instanced else elements(settings.collection, exclude=obj)
    count = settings.count if instanced else len(copies)
    if not count:
        return
    values = engine.audio.values(("cascade", obj.name), settings.audio, engine.driver, count, scene, frame)
    mods = {"reveal": settings.reveal, "spread": 1.0, "twist": 1.0}
    apply_cc_mods(engine.cc_reader, settings.cc, mods)
    mats = matrices(obj.matrix_world, settings, values, mods)
    if not mats:
        return
    influence = engine.influence(obj, 'cascade', settings, scene)
    field_list = fields.gather(engine, settings.attractors, scene, frame)
    if field_list:
        moved = fields.apply(np.array([m.translation for m in mats]), field_list)
        for m, p in zip(mats, moved):
            m.translation = Vector(p)
    t = scene_time(scene, frame)
    cols = colors(settings, values, t) if settings.use_color else None
    if instanced:
        base = obj.matrix_world
        pos, axes, angles, scales = instances.matrices_to_arrays(mats, base.inverted_safe())
        instances.write(settings.instancer, base, pos, axes, angles, scales * influence, colors=cols)
        return
    layer.sync(engine, obj, 'cascade', copies)
    for i, (copy, matrix) in enumerate(zip(copies, mats)):
        layer.place(obj, 'cascade', copy, matrix, frame, settings.is_baking, influence, scene)
        if cols:
            copy.color = cols[i]
