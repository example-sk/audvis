"""Run with Blender --background --factory-startup --python-exit-code 1
--python tests/blender_motion_features_smoke.py
Motion FX features: scatter orbit + morph, beat triggers, attractors, instancing,
cascade layouts, stereo, Grease Pencil scatter, presets and MIDI CC controls.
"""
import importlib
import math
import pathlib
import sys
import time
from types import SimpleNamespace as NS

import bpy
import numpy as np
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
audvis = importlib.import_module(ROOT.name)
preferences = bpy.context.preferences.addons.new()
preferences.module = ROOT.name
audvis.register()
motion = importlib.import_module(ROOT.name + ".analyzer.motion")
audio_mod = importlib.import_module(ROOT.name + ".analyzer.motion.audio")
fields = importlib.import_module(ROOT.name + ".analyzer.motion.fields")

sound = {1: 0.0, 2: 0.0}
cc_values = {}


def fake_driver(*args, ch=1, **kwargs):
    return sound.get(ch, 0.0)


def activate(obj):
    bpy.context.view_layer.objects.active = obj


def co(mesh):
    arr = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)


try:
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 250
    scene.audvis.motion_enable = True
    engine = bpy.audvis._get_motion_engine()
    engine.driver = fake_driver
    engine.cc_reader = lambda control, channel: cc_values.get(control)
    clear_scene()

    # --- beat triggers (audio layer)
    props = NS(source='sound', spread='same', stereo='off', channel=1, freq_start=0, freq_width=10, freq_step=0,
               sound_sequence='', sequence_channel=0, factor=1, response='trigger', threshold=.5,
               trigger_shape="decay", trigger_length=10, cooldown=4, attack=1, release=1, delay=0)
    a = audio_mod.MotionAudio()
    seq = [0, 0, 1, 1, 0, 1, 0, 0, 0, 1]
    out = []
    for f, s in enumerate(seq, start=1):
        sound[1] = s
        out.append(a.values("t", props, fake_driver, 1, NS(frame_start=1), f)[0])
    assert out[2] == 1.0 and out[3] < 1 and out[4] < out[3], out  # hit at frame 3, decays
    assert out[5] < out[4], "re-hit inside cooldown is ignored"
    assert out[9] == 1.0, "fires again after cooldown"
    assert a.values("t", props, fake_driver, 1, NS(frame_start=1), 10)[0] == 1.0, "same frame: no double step"

    # --- stereo routing
    sound[1], sound[2] = 0.0, 1.0
    props.response, props.stereo = 'follow', 'split'
    assert a.values("s", props, fake_driver, 4, NS(frame_start=1), 1) == [0, 0, 1, 1]
    props.stereo = 'alternate'
    assert a.values("s2", props, fake_driver, 4, NS(frame_start=1), 1) == [0, 1, 0, 1]

    # --- fields
    pts = np.array([[3.0, 0, 0], [0, 4.0, 0]])
    f_attract = [{"mode": 'attract', "strength": 1, "center": np.zeros(3), "axis": np.array([0, 0, 1.0]),
                  "radius": 1, "distance": 0, "twist": 0, "influence": 0}]
    assert np.allclose(np.linalg.norm(fields.apply(pts, f_attract), axis=1), 1)
    f_vortex = [dict(f_attract[0], mode='vortex', twist=.25)]
    assert np.allclose(fields.apply(pts, f_vortex)[0], [0, 3, 0], atol=1e-9), "quarter turn"
    f_far = [dict(f_attract[0], influence=1)]
    assert np.allclose(fields.apply(np.array([[5.0, 0, 0]]), f_far), [[5, 0, 0]]), "outside influence"

    # --- cascade layouts
    sound[1] = sound[2] = 0.0
    bpy.ops.mesh.primitive_cube_add(size=.2)
    cube = bpy.context.active_object
    c = cube.audvis.cascade
    c.count, c.layout, c.spacing = 20, 'phyllotaxis', .5
    c.offset, c.rotation, c.scale_step = (0, 0, 0), (0, 0, 0), (1, 1, 1)
    bpy.ops.audvis.motion_cascade_generate()
    copies = sorted(c.collection.objects, key=lambda o: o["audvis_motion_index"])
    assert abs(copies[3].matrix_world.translation.length - .5 * math.sqrt(4)) < 1e-4
    c.layout, c.grid_columns, c.grid_rows, c.spacing = 'grid', 4, 4, 1
    assert (copies[4].matrix_world.translation - Vector((1, 1, 0))).length < 1e-4  # cell 5 = (1, 1)
    curve_data = bpy.data.curves.new("path", 'CURVE')
    spline = curve_data.splines.new('POLY')
    spline.points.add(1)
    spline.points[0].co = (0, 0, 0, 1)
    spline.points[1].co = (10, 0, 0, 1)
    path = bpy.data.objects.new("path", curve_data)
    scene.collection.objects.link(path)
    c.layout, c.curve_object = 'curve', path
    xs = [o.matrix_world.translation.x for o in copies]
    assert abs(xs[0]) < 1e-4 and abs(xs[-1] - 10) < 1e-4 and all(abs(o.matrix_world.translation.y) < 1e-4 for o in copies)

    # --- cascade instances = same transforms as objects
    c.layout = 'chain'
    c.offset, c.rotation, c.scale_step = (0, 0, .3), (0, 0, .3), (.95, .95, .95)
    reference = [o.matrix_world.translation.copy() for o in copies]
    activate(cube)
    c.output = 'instances'
    bpy.ops.audvis.motion_cascade_generate()
    carrier = c.instancer
    assert carrier is not None and not [o for o in c.collection.objects if "audvis_motion_index" in o]
    positions = [carrier.matrix_world @ v.co for v in carrier.data.vertices]
    assert all((p - r).length < 1e-4 for p, r in zip(positions, reference))
    dg = bpy.context.evaluated_depsgraph_get()
    inst = [i.matrix_world.translation.copy() for i in dg.object_instances
            if i.is_instance and i.parent and i.parent.original == carrier]  # instances die after iterating
    assert len(inst) == 20, len(inst)
    assert all(min((p - r).length for p in inst) < 1e-4 for r in reference), "instances where the copies were"
    bpy.ops.audvis.motion_clear(effect='cascade')
    assert c.instancer is None and c.collection is None

    # --- orbit: 10k instances, attractors, CC
    center = bpy.data.objects.new("Center", None)
    scene.collection.objects.link(center)
    activate(center)
    o = center.audvis.orbit
    o.output, o.count = 'instances', 10000
    bpy.ops.audvis.motion_orbit_populate()
    started = time.time()
    for f in range(2, 12):
        scene.frame_set(f)
    per_frame = (time.time() - started) / 10
    dg = bpy.context.evaluated_depsgraph_get()
    n_inst = sum(1 for i in dg.object_instances if i.is_instance and i.parent and i.parent.original == o.instancer)
    assert n_inst == 10000, n_inst
    print("orbit 10k instances: %.1f ms / frame" % (per_frame * 1000))
    bpy.ops.audvis.motion_clear(effect='orbit')
    o.output, o.count = 'objects', 30
    bpy.ops.audvis.motion_orbit_populate()
    sats = list(o.collection.objects)
    bpy.ops.audvis.motion_add_attractor(effect='orbit')
    attractor = o.attractors.objects[0]
    attractor.location = (10, 0, 0)
    attractor.audvis.attractor.sphere_radius = .5
    attractor.audvis.attractor.strength = 1
    bpy.context.view_layer.update()
    motion_ui = importlib.import_module(ROOT.name + ".ui.motion")
    motion_ui.refresh()
    assert all(abs((s.matrix_world.translation - attractor.location).length - .5) < 1e-4 for s in sats)
    attractor.audvis.attractor.strength = 0
    o.cc.enable, o.cc.control, o.cc.target = True, 7, 'gravity'
    o.gravity_stagger, o.gravity_mode, o.sphere_radius = 0, 'core', 1
    cc_values[7] = 1.0
    motion_ui.refresh()
    assert all(s.matrix_world.translation.length < 1e-4 for s in sats), "CC drives gravity"
    cc_values[7] = 0.0
    motion_ui.refresh()
    assert all(s.matrix_world.translation.length > 1 for s in sats)
    o.cc.enable = False

    # --- scatter: orbit, morph, stereo
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1)
    ico = bpy.context.active_object
    s = ico.audvis.scatter
    s.audio.source = 'off'
    bpy.ops.audvis.motion_scatter_prepare()
    rest = co(ico.data)
    s.amount, s.orbit_speed = 1, .5
    scene.frame_set(20)
    a20 = co(ico.data)
    scene.frame_set(21)
    assert not np.allclose(a20, co(ico.data)), "pieces orbit"
    s.amount = 0
    assert np.allclose(co(ico.data), rest, atol=1e-6)
    s.orbit_speed = 0

    bpy.ops.mesh.primitive_cube_add(size=4, location=(0, 0, 0))
    target = bpy.context.active_object
    target.hide_set(True)
    activate(ico)
    s.morph_target, s.morph = target, 1
    cache = engine._cache[("scatter", ico.name)][1]
    morphed = co(ico.data)
    centers = np.stack([np.bincount(cache["pieces"], morphed[:, k]) for k in range(3)], axis=1) \
              / np.bincount(cache["pieces"])[:, None]
    assert np.allclose(np.abs(centers).max(axis=1), 2, atol=1e-3), "pieces sit on the cube surface"
    s.morph = 0
    assert np.allclose(co(ico.data), rest, atol=1e-6)
    s.morph_target = None

    s.audio.source, s.audio.stereo, s.audio.factor, s.audio_amount = 'sound', 'split', 1, 1
    s.audio.release = 1
    scene.audvis.channels = 2
    sound[1], sound[2] = 0.0, 1.0
    scene.frame_set(30)
    moved = np.linalg.norm(co(ico.data) - rest, axis=1) > 1e-4
    piece_x = cache["centers"][cache["pieces"], 0]  # a piece's side is decided by its center
    right, left = piece_x > 1e-6, piece_x < -1e-6
    assert moved[right].all() and not moved[left].any(), "right channel scatters the +X side"
    sound[2] = 0.0

    # --- grease pencil scatter
    gp_data = bpy.data.grease_pencils.new("gp")
    gp = bpy.data.objects.new("gp", gp_data)
    scene.collection.objects.link(gp)
    layer = gp_data.layers.new("L")
    drawing = layer.frames.new(scene.frame_start).drawing
    drawing.add_strokes([3, 3])
    positions = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 1, 0], [1, 1, 0], [2, 1, 0]], dtype=np.float32)
    drawing.attributes["position"].data.foreach_set("vector", positions.ravel())
    activate(gp)
    g = gp.audvis.scatter
    g.audio.source = 'off'
    bpy.ops.audvis.motion_scatter_prepare()

    def gp_co():
        d = gp.data.layers[0].frames[0].drawing
        arr = np.empty(6 * 3, dtype=np.float32)
        d.attributes["position"].data.foreach_get("vector", arr)
        return arr.reshape(-1, 3)

    g.amount = 1
    scattered = gp_co()
    assert not np.allclose(scattered, positions)
    assert abs(np.linalg.norm(scattered[0] - scattered[1]) - 1) < 1e-4, "a stroke moves as one piece"
    g.amount = 0
    assert np.allclose(gp_co(), positions, atol=1e-6)
    bpy.ops.audvis.motion_scatter_remove()
    assert "audvis_rest" not in gp.data.layers[0].frames[0].drawing.attributes

    # --- presets
    presets = importlib.import_module(ROOT.name + ".ui.motion_presets")
    owners = {'cascade': cube, 'orbit': center, 'scatter': ico}
    for effect, items in presets.PRESETS.items():
        for key, *_ in items:
            activate(owners[effect])
            assert bpy.ops.audvis.motion_preset(effect=effect, preset=key) == {'FINISHED'}, (effect, key)
            scene.frame_set(scene.frame_current + 1)

    # --- EQ / macro bands
    eq_ui = importlib.import_module(ROOT.name + ".ui.eq")
    calls = []

    def band_driver(low, high, ch=1, **kwargs):
        calls.append((low, high))
        return 1.0

    eq_props = NS(source='sound', spread='same', stereo='off', channel=1, freq_start=0, freq_width=10,
                  freq_step=0, factor=1.0, sound_sequence='', sequence_channel=0, eq_band='3')
    band3 = scene.audvis.eq_band_3
    band3.gain = .5
    assert audio_mod.MotionAudio(engine).raw_values("eq", eq_props, band_driver, 1, scene, 1) == [.5]
    assert calls[-1] == (150, 400), "uses the band's frequency range"
    band3.mapped, band3.control = True, 21
    cc_values[21] = .75
    assert audio_mod.MotionAudio(engine).raw_values("eq", eq_props, band_driver, 1, scene, 1) == [1.5], \
        "mapped knob overrides the gain slider (0..2)"
    del cc_values[21]
    assert audio_mod.MotionAudio(engine).raw_values("eq", eq_props, band_driver, 1, scene, 1) == [.5], \
        "unmoved knob falls back to the slider"
    eq_props.eq_band = 'off'
    audio_mod.MotionAudio(engine).raw_values("eq", eq_props, band_driver, 1, scene, 1)
    assert calls[-1] == (0, 10)
    cube.audvis.cascade.audio.eq_band = '8'  # real RNA enum
    scene.frame_set(scene.frame_current + 1)
    assert eq_ui.update_meters() == .1

    # Map / Learn must cancel (not raise) when MIDI Realtime goes away while waiting for a knob
    scene.audvis.midi_realtime.enable = False
    fake_ctx = NS(scene=scene, workspace=None, window_manager=NS(windows=[], event_timer_remove=lambda t: None))
    tick = NS(type='TIMER')
    op = NS(band=3, _scene_name=scene.name, _started=time.monotonic(), _timer=None, _start_msg=None,
            report=lambda *a: None, _analyzer=eq_ui.AUDVIS_OT_eqMap._analyzer,
            _finish=lambda ctx: eq_ui.AUDVIS_OT_eqMap._finish(op, ctx))
    assert eq_ui.AUDVIS_OT_eqMap.modal(op, fake_ctx, tick) == {'CANCELLED'}
    ui_motion = importlib.import_module(ROOT.name + ".ui.motion")
    learn = ui_motion.AUDVIS_OT_motionLearnCC
    op = NS(effect='cascade', _obj_name=cube.name, _started=time.time(), _timer=None, _start_msg=None,
            report=lambda *a: None, _analyzer=lambda ctx: learn._analyzer(op, ctx),
            _finish=lambda ctx, cc: learn._finish(op, ctx, cc))
    cube.audvis.cascade.cc.is_learning = True
    assert learn.modal(op, fake_ctx, tick) == {'CANCELLED'}
    assert not cube.audvis.cascade.cc.is_learning

    assert not engine._reported, "an effect raised: %s" % engine._reported
    print("PASS: Motion FX features", bpy.app.version_string)
finally:
    audvis.unregister()
    bpy.context.preferences.addons.remove(preferences)
