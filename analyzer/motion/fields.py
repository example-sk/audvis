"""Attractors: objects that bend the positions computed by an effect.

Each attractor (any object, usually an Empty) has a mode:
- attract: pull onto a sphere shell around the attractor
- repel: push away
- vortex: swirl around the attractor's local Z axis
Strength 0..1 (keyframe it, drive it by sound / MIDI CC) and an influence radius
(0 = everywhere). Attractors are applied in order, so later ones win - keyframe
the strengths of two attractors against each other to move a swarm between them.
They are pure functions of position, so everything stays scrubbable."""
import math

import numpy as np
from mathutils import Vector

from .audio import apply_cc
from .lib import elements


def gather(engine, collection, scene, frame):
    out = []
    for obj in elements(collection):
        s = obj.audvis.attractor
        strength = s.strength
        if s.audio.source != 'off':
            strength += s.audio_strength * engine.audio.values(("attractor", obj.name), s.audio, engine.driver,
                                                               1, scene, frame)[0]
        strength = apply_cc(engine.cc_reader, s.cc, strength)
        if abs(strength) < 1e-6:
            continue
        m = obj.matrix_world
        out.append({
            "mode": s.mode,
            "strength": strength,
            "center": np.array(m.translation),
            "axis": np.array((m.to_3x3() @ Vector((0, 0, 1))).normalized()),
            "radius": s.sphere_radius,
            "distance": s.distance,
            "twist": s.twist,
            "influence": s.influence,
        })
    return out


def _falloff(d, influence):
    if influence <= 0:
        return np.ones_like(d)
    x = np.clip(2 - d / influence, 0, 1)  # full inside the radius, fades out until twice the radius
    return x * x * (3 - 2 * x)


def apply(points, fields, weight=None):
    """Bend world-space points (n, 3). weight (n,) scales the influence per point."""
    if not fields or not len(points):
        return points
    points = np.array(points, dtype=float)
    for f in fields:
        rel = points - f["center"]
        d = np.linalg.norm(rel, axis=1)
        k = _falloff(d, f["influence"]) * f["strength"]
        if weight is not None:
            k = k * weight
        unit = rel / np.maximum(d, 1e-9)[:, None]
        if f["mode"] == 'attract':
            k = np.clip(k, -1, 1)
            target = f["center"] + unit * f["radius"]
            points += (target - points) * k[:, None]
        elif f["mode"] == 'repel':
            points += unit * (f["distance"] * k)[:, None]
        else:  # vortex
            angle = 2 * math.pi * f["twist"] * k
            axis = np.broadcast_to(f["axis"], rel.shape)
            cos, sin = np.cos(angle)[:, None], np.sin(angle)[:, None]
            dot = np.sum(axis * rel, axis=1, keepdims=True)
            points = f["center"] + rel * cos + np.cross(axis, rel) * sin + axis * dot * (1 - cos)
    return points


def apply_local(points_local, matrix, fields, weight=None):
    """Same as apply() for points in an object's local space."""
    if not fields:
        return points_local
    m = np.array(matrix)
    world = points_local @ m[:3, :3].T + m[:3, 3]
    world = apply(world, fields, weight)
    inv = np.linalg.inv(m)
    return world @ inv[:3, :3].T + inv[:3, 3]
