"""Scatter: tear a mesh (or Grease Pencil drawing) apart into pieces and put it
back together - or together as another shape (morph target).

Amount 0 is the untouched shape, amount 1 fully scattered. The rest positions and
piece ids are stored as attributes, so the effect is a pure function of the
amount and time - it can be scrubbed."""
import math

import numpy as np

from . import fields, fluid, morph
from .audio import apply_cc_mods
from .lib import scene_time

REST = "audvis_rest"
PIECE = "audvis_piece"
MIN_SCALE = 1e-4


def _read(collection, attr, n, width, dtype=np.float32):
    arr = np.empty(n * width, dtype=dtype)
    collection.foreach_get(attr, arr)
    return arr.reshape(n, width) if width > 1 else arr


def islands(n, edges):
    """Connected-component id per vertex (label propagation with pointer jumping)."""
    labels = np.arange(n)
    if not len(edges):
        return labels
    a, b = edges[:, 0], edges[:, 1]
    while True:
        new = labels.copy()
        low = np.minimum(labels[a], labels[b])
        np.minimum.at(new, a, low)
        np.minimum.at(new, b, low)
        new = new[new]
        if np.array_equal(new, labels):
            break
        labels = new
    return np.unique(labels, return_inverse=True)[1]


def _store(attributes, rest, pieces):
    for name in (REST, PIECE):
        if name in attributes:
            attributes.remove(attributes[name])
    attributes.new(REST, 'FLOAT_VECTOR', 'POINT').data.foreach_set("vector", np.asarray(rest, np.float32).ravel())
    attributes.new(PIECE, 'INT', 'POINT').data.foreach_set("value", np.asarray(pieces, np.int32))


def _has(attributes):
    return REST in attributes and PIECE in attributes


# ---------------------------------------------------------------- meshes

def is_prepared(mesh):
    return mesh is not None and _has(mesh.attributes)


def prepare(mesh, mode):
    """Split the mesh (for 'faces') and store rest positions + piece ids."""
    import bmesh
    if mode == 'faces':
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.split_edges(bm, edges=bm.edges[:])
        bm.to_mesh(mesh)
        bm.free()
    n = len(mesh.vertices)
    if mode == 'vertices':
        pieces = np.arange(n)
    else:
        pieces = islands(n, _read(mesh.edges, "vertices", len(mesh.edges), 2, np.int32))
    _store(mesh.attributes, _read(mesh.vertices, "co", n, 3), pieces)
    mesh.update()


def _mesh_face_normals(mesh, rest, pieces, count):
    """Per-piece normal and total face area, from the rest shape (current vertex
    normals may be scattered)."""
    normals = np.zeros((count, 3))
    if not len(mesh.polygons):
        return normals, 0.0
    starts = _read(mesh.polygons, "loop_start", len(mesh.polygons), 1, np.int32)
    totals = _read(mesh.polygons, "loop_total", len(mesh.polygons), 1, np.int32)
    loops = _read(mesh.loops, "vertex_index", len(mesh.loops), 1, np.int32)
    ok = totals >= 3
    v0, v1, v2 = (loops[starts[ok] + k] for k in range(3))
    face_n = np.cross(rest[v1] - rest[v0], rest[v2] - rest[v0])
    np.add.at(normals, pieces[v0], face_n)
    area = float((np.linalg.norm(face_n, axis=1) / 2 * (totals[ok] - 2)).sum())  # n-gon ~ n-2 triangles
    return normals, area


def mesh_cache(mesh, seed):
    n = len(mesh.vertices)
    rest = _read(mesh.attributes[REST].data, "vector", n, 3).astype(np.float64)
    pieces = _read(mesh.attributes[PIECE].data, "value", n, 1, np.int32)
    count = int(pieces.max()) + 1 if n else 0
    normals, area = _mesh_face_normals(mesh, rest, pieces, count)
    return build_cache(rest, pieces, normals, area, seed)


# ---------------------------------------------------------------- grease pencil (Blender 4.3+)

def gp_supported(obj):
    return obj is not None and obj.type == 'GREASEPENCIL'


def gp_drawings(obj):
    for layer in obj.data.layers:
        for frame in layer.frames:
            if frame.drawing is not None:
                yield layer, frame, frame.drawing


def gp_is_prepared(obj):
    return gp_supported(obj) and any(_has(d.attributes) for _, _, d in gp_drawings(obj))


def gp_prepare(obj, mode):
    """Pieces are strokes ('faces' / 'islands') or single points ('vertices')."""
    for _, _, drawing in gp_drawings(obj):
        n = len(drawing.attributes["position"].data) if "position" in drawing.attributes else 0
        if not n:
            continue
        offsets = _read(drawing.curve_offsets, "value", len(drawing.curve_offsets), 1, np.int32)
        if mode == 'vertices':
            pieces = np.arange(n)
        else:
            pieces = np.repeat(np.arange(len(offsets) - 1), np.diff(offsets))
        _store(drawing.attributes, _read(drawing.attributes["position"].data, "vector", n, 3), pieces)


def gp_cache(drawing, seed):
    n = len(drawing.attributes[REST].data)
    rest = _read(drawing.attributes[REST].data, "vector", n, 3).astype(np.float64)
    pieces = _read(drawing.attributes[PIECE].data, "value", n, 1, np.int32)
    count = int(pieces.max()) + 1 if n else 0
    return build_cache(rest, pieces, np.zeros((count, 3)), 0.0, seed)


def gp_write(drawing, co):
    drawing.attributes["position"].data.foreach_set("vector", np.asarray(co, np.float32).ravel())
    drawing.tag_positions_changed()


def gp_restore(obj, remove=False):
    for _, _, drawing in gp_drawings(obj):
        if _has(drawing.attributes):
            n = len(drawing.attributes[REST].data)
            gp_write(drawing, _read(drawing.attributes[REST].data, "vector", n, 3))
            if remove:
                for name in (REST, PIECE):
                    drawing.attributes.remove(drawing.attributes[name])


# ---------------------------------------------------------------- shared math

def build_cache(rest, pieces, normals, area, seed):
    n = len(rest)
    count = int(pieces.max()) + 1 if n else 0
    sizes = np.maximum(np.bincount(pieces, minlength=count), 1)[:, None]
    centers = np.stack([np.bincount(pieces, rest[:, k], count) for k in range(3)], axis=1) / sizes

    rng = np.random.default_rng(seed)
    random_dir = rng.normal(size=(count, 3))
    axis = rng.normal(size=(count, 3))
    orbit_axis = rng.normal(size=(count, 3))
    outward = centers.copy()
    normals = normals.copy()
    piece_normals = normals.copy()
    for arr, fallback in ((random_dir, None), (axis, None), (orbit_axis, None),
                          (outward, random_dir), (normals, outward)):
        length = np.linalg.norm(arr, axis=1, keepdims=True)
        if fallback is not None:
            arr[:] = np.where(length > 1e-9, arr, fallback)
            length = np.linalg.norm(arr, axis=1, keepdims=True)
        arr /= np.maximum(length, 1e-9)
    length = np.linalg.norm(piece_normals, axis=1, keepdims=True)
    piece_normals = np.where(length > 1e-9, piece_normals / np.maximum(length, 1e-9), 0)  # 0 = no face

    dist = np.linalg.norm(centers, axis=1)
    z = centers[:, 2] if count else np.zeros(0)
    return {
        "n": n,
        "rest": rest,
        "pieces": pieces,
        "centers": centers,
        "piece_normals": piece_normals,
        "area": area,
        "dirs": {"outward": outward, "normal": normals, "random": random_dir},
        "axis": axis,
        "orbit_axis": orbit_axis,
        "jitter": rng.random(count) * 2 - 1,
        "spin": rng.random(count) * 2 - 1,
        "phase": rng.random((count, 3)),
        "side": (centers[:, 0] >= 0).astype(int) if count else np.zeros(0, int),
        "order": {
            "distance": dist / max(dist.max(), 1e-9) if count else dist,
            "z": (z - z.min()) / max(np.ptp(z), 1e-9) if count else z,
            "random": rng.random(count),
        },
        "at_rest": False,
        "morph": None,
    }


def _rotate(vectors, axis, angle):
    """Rodrigues rotation of each vector around its own unit axis."""
    cos = np.cos(angle)[:, None]
    sin = np.sin(angle)[:, None]
    dot = np.sum(axis * vectors, axis=1, keepdims=True)
    return vectors * cos + np.cross(axis, vectors) * sin + axis * dot * (1 - cos)


def piece_order(settings, cache):
    order = cache["order"][settings.stagger_mode]
    return 1 - order if settings.stagger_invert else order


def element_count(settings):
    """How many audio values Scatter asks for: groups by stagger order, x2 for stereo."""
    groups = settings.audio_elements if settings.audio.spread != 'same' else 1
    return groups * (2 if settings.audio.stereo != 'off' and settings.audio.source == 'sound' else 1)


def piece_values(settings, cache, values):
    """Map audio values to pieces: group by stagger order, left / right by the side
    of the object the piece is on (matches audio.channel_layout)."""
    values = np.asarray(values, dtype=float)
    order = piece_order(settings, cache)
    stereo = settings.audio.stereo != 'off' and settings.audio.source == 'sound'
    groups = len(values) // 2 if stereo else len(values)
    group = np.minimum((order * groups).astype(int), groups - 1)
    if not stereo:
        return values[group]
    side = cache["side"]
    if settings.audio.stereo == 'split':
        return values[group + groups * side]
    return values[group * 2 + side]


def _staggered(settings, cache, amount):
    if settings.stagger <= 0:
        return np.clip(amount, 0, 1)
    order = piece_order(settings, cache)
    return np.clip(amount * (1 + settings.stagger) - order * settings.stagger, 0, 1)


def _ease(x):
    return x * x * (3 - 2 * x)


def compute(settings, cache, values, t, mods=None, matrix=None, field_list=None):
    """New vertex positions, or None if every piece is at rest."""
    mods = mods or {"amount": settings.amount, "morph": settings.morph, "distance": 1.0}
    v = piece_values(settings, cache, values)
    ease = _ease(_staggered(settings, cache, mods["amount"] + settings.audio_amount * v))
    target = cache.get("morph")
    morph_e = np.zeros_like(ease)
    if target is not None:
        morph_e = _ease(_staggered(settings, cache, mods["morph"] + settings.audio_morph * v))
    lift = np.maximum(ease, settings.morph_scatter * np.sin(math.pi * morph_e))  # fly while morphing
    if not lift.any() and not morph_e.any():
        return None

    if settings.direction == 'vector':
        vec = np.array(settings.direction_vector, dtype=float)
        dirs = np.broadcast_to(vec / max(np.linalg.norm(vec), 1e-9), cache["centers"].shape)
    else:
        dirs = cache["dirs"][settings.direction]
    if settings.direction_random > 0:
        dirs = dirs + (cache["dirs"]["random"] - dirs) * settings.direction_random
        dirs = dirs / np.maximum(np.linalg.norm(dirs, axis=1, keepdims=True), 1e-9)

    centers = cache["centers"]
    base = centers
    rel_scale = 1 - settings.shrink * ease
    if target is not None:
        base = centers + (target["centers"] - centers) * morph_e[:, None]
        rel_scale = rel_scale * (1 + (target["fit"] * settings.morph_scale - 1) * morph_e)

    distance = settings.distance * mods["distance"] * (1 + settings.distance_random * cache["jitter"])
    full = base + dirs * distance[:, None]
    if settings.turbulence > 0:
        full = full + np.sin(2 * math.pi * (settings.turbulence_speed * t + cache["phase"])) * settings.turbulence
    if settings.orbit_speed != 0:  # scatter into orbit: the scattered positions circle the origin
        axis = np.array([0.0, 0.0, 1.0]) + cache["orbit_axis"] * settings.orbit_tilt
        axis /= np.maximum(np.linalg.norm(axis, axis=1, keepdims=True), 1e-9)
        radius = np.maximum(np.linalg.norm(full, axis=1), 1e-6)
        ref = max(float(np.median(radius)), 1e-6)
        angle = 2 * math.pi * settings.orbit_speed * t * (ref / radius) ** 1.5 * (1 + .3 * cache["jitter"])
        full = _rotate(full, axis, angle)
    new_centers = base + (full - base) * lift[:, None]
    if field_list:
        new_centers = fields.apply_local(new_centers, matrix, field_list, weight=lift)

    angle = cache["spin"] * lift * (math.radians(settings.rotation) + 2 * math.pi * settings.tumble_speed * t)
    pieces = cache["pieces"]
    rel = cache["rest"] - centers[pieces]
    if target is not None:
        rel = _rotate(rel, target["axis"][pieces], (target["angle"] * morph_e)[pieces])
    rel = _rotate(rel, cache["axis"][pieces], angle[pieces])
    return new_centers[pieces] + rel * np.maximum(MIN_SCALE, rel_scale)[pieces][:, None]


def _ensure_morph(settings, cache, owner_matrix):
    target = settings.morph_target
    if target is None or target.type != 'MESH':
        cache["morph"] = None
        return
    signature = (target.name, len(target.data.vertices), settings.seed,
                 tuple(round(x, 5) for row in owner_matrix.inverted_safe() @ target.matrix_world for x in row))
    if cache.get("morph_signature") != signature:
        cache["morph_signature"] = signature
        cache["morph"] = morph.build(target, owner_matrix, cache["centers"], cache["piece_normals"],
                                     cache["area"], settings.seed)


def compute_fluid(settings, cache, values, t, mods, matrix, field_list, scene, frame):
    """Fluid style: pieces drift in a Navier-Stokes flow driven by sound (see fluid.py)."""
    signature = (settings.fluid_resolution, round(settings.fluid_domain, 4), settings.seed)
    flow = cache.get("flow")
    if flow is None or cache.get("flow_signature") != signature:
        flow = cache["flow"] = fluid.Flow(cache["centers"], settings.fluid_resolution, settings.fluid_domain,
                                          settings.seed)
        cache["flow_signature"] = signature
        flow.frame = frame
    centers = cache["centers"]
    v = piece_values(settings, cache, values)
    energy = float(np.mean(values)) if len(values) else 0.0
    push = v - energy if settings.audio.spread != 'same' else None  # each band kicks its own pieces
    targets, scale = centers, 1 - settings.shrink * min(1.0, mods["amount"])
    target = cache.get("morph")
    if target is not None:
        morph_e = _ease(_staggered(settings, cache, mods["morph"] + settings.audio_morph * v))
        targets = centers + (target["centers"] - centers) * morph_e[:, None]
        scale = scale * (1 + (target["fit"] * settings.morph_scale - 1) * morph_e)
    fps = scene.render.fps / scene.render.fps_base

    def run_step(dt):
        flow.step(settings, energy, t, dt, targets, push, flow=mods["amount"])

    if not flow.advance(frame, scene.frame_start, scene.frame_end, fps, run_step, settings.fluid_keep_on_loop):
        flow.reset(centers, frame)
    positions = flow.pos
    if field_list:
        positions = fields.apply_local(positions, matrix, field_list, weight=np.ones(len(positions)))
    return flow.vertices(cache["rest"], centers, cache["pieces"], positions, scale)


def _run(engine, obj, settings, cache, values, t, mods, field_list, write, influence=1.0, scene=None, frame=None):
    _ensure_morph(settings, cache, obj.matrix_world)
    if settings.style == 'fluid' and scene is not None:
        co = compute_fluid(settings, cache, values, t, mods, obj.matrix_world, field_list, scene, frame)
    else:
        co = compute(settings, cache, values, t, mods, obj.matrix_world, field_list)
    if co is not None and influence < 1:  # fade towards the assembled shape
        co = None if influence <= 0 else cache["rest"] + (co - cache["rest"]) * influence
    if co is None:
        if not cache["at_rest"]:
            write(cache["rest"])
            cache["at_rest"] = True
        return
    cache["at_rest"] = False
    write(co)


def update(engine, obj, scene, frame):
    settings = obj.audvis.scatter
    key = ("scatter", obj.name)
    values = engine.audio.values(key, settings.audio, engine.driver, element_count(settings), scene, frame)
    mods = {"amount": settings.amount, "morph": settings.morph, "distance": 1.0}
    apply_cc_mods(engine.cc_reader, settings.cc, mods)
    field_list = fields.gather(engine, settings.attractors, scene, frame)
    t = scene_time(scene, frame)
    influence = engine.influence(obj, 'scatter', settings, scene)
    if obj.type == 'MESH':
        mesh = obj.data
        if not is_prepared(mesh):
            return
        cache = engine.cached(key, (mesh.name, len(mesh.vertices), settings.seed, settings.prepared_id),
                              lambda: mesh_cache(mesh, settings.seed))
        _run(engine, obj, settings, cache, values, t, mods, field_list, lambda co: write(mesh, co), influence,
             scene, frame)
    elif gp_supported(obj):
        for layer in obj.data.layers:
            gp_frame = layer.current_frame()
            if gp_frame is None or gp_frame.drawing is None or not _has(gp_frame.drawing.attributes):
                continue
            drawing = gp_frame.drawing
            n = len(drawing.attributes[REST].data)
            cache = engine.cached(key + (layer.name, gp_frame.frame_number),
                                  (n, settings.seed, settings.prepared_id), lambda: gp_cache(drawing, settings.seed))
            _run(engine, obj, settings, cache, values, t, mods, field_list, lambda co: gp_write(drawing, co),
                 influence, scene, frame)


def write(mesh, co):
    mesh.vertices.foreach_set("co", np.asarray(co, np.float32).ravel())
    mesh.update()


def restore(obj):
    if obj.type == 'MESH':
        mesh = obj.data
        if is_prepared(mesh):
            write(mesh, _read(mesh.attributes[REST].data, "vector", len(mesh.vertices), 3))
    elif gp_supported(obj):
        gp_restore(obj)
