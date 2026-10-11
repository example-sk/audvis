"""Run with Blender --background --factory-startup --python-exit-code 1
--python tests/blender_motion_smoke.py
Exercises Motion FX (cascade, scatter, orbit + gravity, baking) with a fake audio driver.
"""
import importlib
import math
import pathlib
import sys

import bpy
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
audvis = importlib.import_module(ROOT.name)
preferences = bpy.context.preferences.addons.new()
preferences.module = ROOT.name
audvis.register()

sound = [0.0]


def fake_driver(*args, **kwargs):
    return sound[0]


def activate(obj):
    bpy.context.view_layer.objects.active = obj


try:
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 10
    engine = bpy.audvis._get_motion_engine()
    engine.driver = fake_driver

    # --- cascade
    bpy.ops.mesh.primitive_cube_add(size=1)
    cube = bpy.context.active_object
    c = cube.audvis.cascade
    c.count = 5
    c.offset = (0, 0, 1)
    c.rotation = (0, 0, 0)
    c.scale_step = (1, 1, 1)
    c.audio.factor = 1
    bpy.ops.audvis.motion_cascade_generate()
    copies = sorted(c.collection.objects, key=lambda o: o["audvis_motion_index"])
    assert len(copies) == 5 and all(not o.audvis.cascade.enable for o in copies)
    assert all(o.data == cube.data for o in copies), "linked copies share data"
    sound[0] = 1.0
    scene.frame_set(2)
    # offset (0,0,1) stretched by 1 + audio_offset(1) * 1 = 2 per copy
    assert abs(copies[2].matrix_world.translation.z - 6) < 1e-4, copies[2].matrix_world.translation
    c.reveal = .5
    assert copies[4].matrix_world.to_scale().x < .01, "second half hidden by reveal"
    c.reveal = 1

    # bake: the engine inserts keyframes while is_baking is set
    c.is_baking = True
    engine.audio.reset()
    for f in range(1, 4):
        scene.frame_set(f)
    c.is_baking = False
    assert copies[0].animation_data and copies[0].animation_data.action
    bpy.ops.audvis.motion_clear(effect='cascade')
    assert c.collection is None and not [o for o in bpy.data.objects if "cascade" in o.name]

    # --- orbit + gravity sphere
    sound[0] = 0.0
    center = bpy.data.objects.new("Center", None)
    scene.collection.objects.link(center)
    activate(center)
    o = center.audvis.orbit
    o.count = 30
    o.radius_min, o.radius_max = 2, 5
    bpy.ops.audvis.motion_orbit_populate()
    sats = list(o.collection.objects)
    assert len(sats) == 30 and center.empty_display_type == 'SPHERE'

    def distances():
        return [s.matrix_world.translation.length for s in sats]

    scene.frame_set(3)
    assert all(2 - 1e-4 <= d <= 5 + 1e-4 for d in distances()), distances()
    first = sats[0].matrix_world.translation.copy()
    scene.frame_set(20)
    assert (sats[0].matrix_world.translation - first).length > 1e-3, "satellites move"
    o.gravity = 1
    o.sphere_radius = 1.5
    assert all(abs(d - 1.5) < 1e-4 for d in distances()), "all on the sphere shell"
    o.gravity_mode = 'core'
    assert all(d < 1e-4 for d in distances()) and sats[0].matrix_world.to_scale().x < .01
    o.gravity = 0
    o.audio_gravity = 1
    o.audio.factor = 1
    o.gravity_mode = 'radial'
    sound[0] = 1.0
    scene.frame_set(21)
    assert all(abs(d - 1.5) < 1e-4 for d in distances()), "sound pulls everything in"

    # --- scatter
    sound[0] = 0.0
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1)
    ico = bpy.context.active_object
    faces, verts = len(ico.data.polygons), len(ico.data.vertices)
    s = ico.audvis.scatter
    bpy.ops.audvis.motion_scatter_prepare()
    mesh = ico.data
    assert len(mesh.vertices) == faces * 3, "faces torn apart"
    pieces = np.empty(len(mesh.vertices), dtype=np.int32)
    mesh.attributes["audvis_piece"].data.foreach_get("value", pieces)
    assert len(set(pieces.tolist())) == faces

    def co():
        arr = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get("co", arr)
        return arr.reshape(-1, 3)

    rest = co()
    s.amount = 1
    scattered = co()
    assert np.linalg.norm(scattered - rest, axis=1).min() > .1, "every piece moved"
    # a shard keeps its shape (rigid motion): edge lengths survive
    a, b = mesh.polygons[0].vertices[:2]
    assert abs(np.linalg.norm(scattered[a] - scattered[b]) - np.linalg.norm(rest[a] - rest[b])) < 1e-4
    s.amount = 0
    assert np.allclose(co(), rest, atol=1e-6), "reassembled"
    s.audio_amount = 1
    s.audio.factor = 1
    sound[0] = 1.0
    scene.frame_set(22)
    assert not np.allclose(co(), rest), "sound scatters"
    s.piece_mode = 'islands'
    bpy.ops.audvis.motion_scatter_prepare()
    assert len(ico.data.vertices) == verts, "prepared again from the original"
    pieces = np.empty(verts, dtype=np.int32)
    ico.data.attributes["audvis_piece"].data.foreach_get("value", pieces)
    assert len(set(pieces.tolist())) == 1, "an ico sphere is one island"
    bpy.ops.audvis.motion_scatter_remove()
    assert "audvis_rest" not in ico.data.attributes and s.original_mesh is None

    assert not engine._reported, "an effect raised: %s" % engine._reported
    print("PASS: Motion FX cascade, bake, orbit gravity, scatter", bpy.app.version_string)
finally:
    audvis.unregister()
    bpy.context.preferences.addons.remove(preferences)
