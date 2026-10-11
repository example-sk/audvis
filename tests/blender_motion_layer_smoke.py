"""Run with Blender --background --factory-startup --python-exit-code 1
--python tests/blender_motion_layer_smoke.py
Motion FX override layer: effects override the user's own animation through constraints,
fade with Influence / Engage / Release / Master, and stop with that animation intact.
"""
import importlib
import pathlib
import sys
import time
from types import SimpleNamespace as NS

import bpy
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
audvis = importlib.import_module(ROOT.name)
preferences = bpy.context.preferences.addons.new()
preferences.module = ROOT.name
audvis.register()
layer = importlib.import_module(ROOT.name + ".analyzer.motion.layer")
ui_motion = importlib.import_module(ROOT.name + ".ui.motion")
utils = importlib.import_module(ROOT.name + ".utils")

cc_values = {}


def ev(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    return np.array(obj.evaluated_get(dg).matrix_world.translation)


def own(obj):
    """Where the object's own animation / transform puts it (constraints muted)."""
    cons = [c for c in obj.constraints if not c.mute]
    for c in cons:
        c.mute = True
    bpy.context.view_layer.update()
    pos = ev(obj)
    for c in cons:
        c.mute = False
    bpy.context.view_layer.update()
    return pos


def key_count(obj):
    action = obj.animation_data.action
    return sum(len(fc.keyframe_points) for fc in utils.action_get_fcurves(action))


class MockLayout:
    """Accepts any layout call; prop() checks the property exists, so draw code typos fail the test."""

    def __getattr__(self, name):
        if name == 'prop':
            def prop(data, prop_name, **kwargs):
                assert prop_name in data.bl_rna.properties, prop_name
                return MockLayout()
            return prop
        return lambda *args, **kwargs: MockLayout()

    def __setattr__(self, name, value):
        pass


try:
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 50
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    engine = bpy.audvis._get_motion_engine()
    engine.driver = lambda *args, **kwargs: 0.0
    engine.cc_reader = lambda control, channel: cc_values.get(control)

    mine = bpy.data.collections.new("Mine")
    scene.collection.children.link(mine)
    keyed = bpy.data.objects.new("Keyed", None)
    mine.objects.link(keyed)
    keyed.location = (0, 0, 0)
    keyed.keyframe_insert("location", frame=1)
    keyed.location = (0, 0, 10)
    keyed.keyframe_insert("location", frame=50)
    plain = bpy.data.objects.new("Plain", None)
    mine.objects.link(plain)
    plain.location = (5, 5, 5)
    center = bpy.data.objects.new("Center", None)
    scene.collection.objects.link(center)
    bpy.context.view_layer.objects.active = center
    orbit = center.audvis.orbit
    orbit.collection = mine
    orbit.radius_min = orbit.radius_max = 3
    scene.audvis.motion_enable = True
    orbit.enable = True
    keys_before = key_count(keyed)

    # --- 1. the effect overrides keyframed and plain objects without writing their transforms
    scene.frame_set(25)
    assert np.linalg.norm(ev(keyed) - own(keyed)) > 1, "orbit must override the keyframes"
    assert abs(np.linalg.norm(ev(plain)) - 3) < 1e-3, "plain object orbits at radius 3"
    assert tuple(plain.location) == (5, 5, 5), "the user's own transform is never written"
    assert np.allclose(own(keyed), (0, 0, keyed.location.z)), "keyframes still drive the property"
    assert layer.summary(scene) == (2, 0)

    # --- 2. Influence crossfades between the effect and the object's own animation
    full = ev(plain)
    orbit.influence = .5
    scene.frame_set(25)
    assert np.allclose(ev(plain), (full + np.array((5, 5, 5))) / 2, atol=1e-3)
    orbit.influence = 1

    # --- 3. Master scales every effect
    scene.audvis.motion_master = 0
    scene.frame_set(25)
    assert np.allclose(ev(plain), (5, 5, 5)) and np.allclose(ev(keyed), own(keyed))
    scene.audvis.motion_master = 1

    # --- 4. MIDI CC can drive Influence
    orbit.cc.enable, orbit.cc.control, orbit.cc.target = True, 9, 'influence'
    orbit.cc.mode, orbit.cc.range_min, orbit.cc.range_max = 'replace', 0, 1
    cc_values[9] = 0.0
    scene.frame_set(26)
    assert np.allclose(ev(plain), (5, 5, 5))
    orbit.cc.enable = False

    # --- 5. switching off hands the objects back: own animation intact, nothing left over
    scene.frame_set(27)
    orbit.enable = False
    scene.frame_set(28)
    assert np.allclose(ev(plain), (5, 5, 5)), "plain object back where the user put it"
    assert np.allclose(ev(keyed), own(keyed)) and 0 < ev(keyed)[2] < 10, "keyed object plays its keyframes"
    assert key_count(keyed) == keys_before

    # --- 6. Stop / Engage buttons, Release with a fade over wall time
    orbit.enable = True
    scene.frame_set(29)
    assert bpy.ops.audvis.motion_fade(action='stop', effect='all') == {'FINISHED'}
    assert not orbit.enable and ("Center", 'orbit') in engine.released
    scene.frame_set(30)
    assert np.allclose(ev(plain), (5, 5, 5))
    scene.audvis.motion_fade_time = 0
    assert bpy.ops.audvis.motion_fade(action='engage', effect='all') == {'FINISHED'}
    assert orbit.enable and not engine.released
    scene.frame_set(31)
    assert abs(np.linalg.norm(ev(plain)) - 3) < 1e-3
    scene.audvis.motion_fade_time = .2
    bpy.ops.audvis.motion_fade(action='release', effect='orbit', object_name="Center")
    scene.frame_set(32)
    assert orbit.enable, "still fading"
    time.sleep(.25)
    scene.frame_set(33)
    assert not orbit.enable, "a finished Release switches the effect off"
    scene.frame_set(34)
    assert np.allclose(ev(plain), (5, 5, 5))
    bpy.ops.audvis.motion_fade(action='engage', effect='all')
    assert orbit.enable
    scene.frame_set(35)
    time.sleep(.25)
    scene.frame_set(36)
    assert engine.gate("Center", 'orbit') == 1.0 and abs(np.linalg.norm(ev(plain)) - 3) < 1e-3

    # --- 7. objects leaving the effect's collection are released
    mine.objects.unlink(plain)
    scene.collection.objects.link(plain)
    scene.frame_set(37)
    assert np.allclose(ev(plain), (5, 5, 5))
    scene.collection.objects.unlink(plain)
    mine.objects.link(plain)

    # --- 8. the master switch stops everything
    scene.audvis.motion_enable = False
    scene.frame_set(38)
    assert np.allclose(ev(plain), (5, 5, 5)) and np.allclose(ev(keyed), own(keyed))
    scene.audvis.motion_enable = True

    # --- 9. bake goes onto the helpers, never into the user's action
    for f in range(1, 51):
        orbit.is_baking = True
        scene.frame_set(f)
    orbit.is_baking = False
    orbit.enable = False  # like the bake operator
    assert key_count(keyed) == keys_before, "user's action untouched"
    assert layer.summary(scene) == (0, 2)
    scene.frame_set(20)
    assert abs(np.linalg.norm(ev(plain)) - 3) < 1e-3, "baked override plays with the effect off"
    assert bpy.ops.audvis.motion_layer_remove(effect='all') == {'FINISHED'}
    assert not keyed.constraints and not plain.constraints
    assert not any(c.get(layer.LAYER_KEY) for c in bpy.data.collections), "helpers cleaned up"
    scene.frame_set(21)
    assert np.allclose(ev(plain), (5, 5, 5)) and np.allclose(ev(keyed), own(keyed))

    # --- 10. generated copies shrink with Influence (they have no animation of their own)
    cube = bpy.data.objects.new("Src", bpy.data.meshes.new("Src"))
    scene.collection.objects.link(cube)
    bpy.context.view_layer.objects.active = cube
    cube.audvis.cascade.count = 3
    assert bpy.ops.audvis.motion_cascade_generate() == {'FINISHED'}
    copies = [o for o in cube.audvis.cascade.collection.objects]
    scene.frame_set(22)
    size = copies[0].matrix_world.to_scale().x
    cube.audvis.cascade.influence = .5
    scene.frame_set(23)
    assert abs(copies[0].matrix_world.to_scale().x - size / 2) < 1e-4
    assert not any(o.constraints for o in copies), "AudVis copies are placed directly"

    # --- 11. scatter fades back to the assembled shape
    bpy.ops.mesh.primitive_ico_sphere_add()
    ico = bpy.context.active_object
    assert bpy.ops.audvis.motion_scatter_prepare() == {'FINISHED'}
    s = ico.audvis.scatter
    s.amount = 1
    scene.frame_set(24)
    rest = np.empty(len(ico.data.vertices) * 3, np.float32)
    ico.data.attributes["audvis_rest"].data.foreach_get("vector", rest)
    co = np.empty_like(rest)
    ico.data.vertices.foreach_get("co", co)
    assert not np.allclose(co, rest)
    s.influence = 0
    scene.frame_set(25)
    ico.data.vertices.foreach_get("co", co)
    assert np.allclose(co, rest, atol=1e-5)

    # --- 12. every panel draws (catches typos in the GUI code)
    orbit.enable = True
    scene.frame_set(26)
    for obj in (center, cube, ico):
        ctx = NS(scene=scene, active_object=obj, object=obj, window=NS(audvis=NS(iseq=False)))
        for panel in (ui_motion.AUDVIS_PT_motionNpanel, ui_motion.AUDVIS_PT_motionCascadeNpanel,
                      ui_motion.AUDVIS_PT_motionOrbitNpanel, ui_motion.AUDVIS_PT_motionScatterNpanel):
            if panel.poll(ctx):
                panel.draw(NS(layout=MockLayout()), ctx)

    assert not engine._reported, "an effect raised: %s" % engine._reported
    print("PASS: Motion FX override layer", bpy.app.version_string)
finally:
    audvis.unregister()
    bpy.context.preferences.addons.remove(preferences)
