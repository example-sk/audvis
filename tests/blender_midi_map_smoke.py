"""Run with Blender --background --factory-startup --python-exit-code 1
--python tests/blender_midi_map_smoke.py
MIDI Mappings on real properties (AudVis and native), with a fake MIDI input thread.
"""
import collections
import importlib
import pathlib
import sys
from types import SimpleNamespace as NS

import bpy

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
audvis = importlib.import_module(ROOT.name)
preferences = bpy.context.preferences.addons.new()
preferences.module = ROOT.name
audvis.register()
mapping = importlib.import_module(ROOT.name + ".ui.midi.mapping")
map_mode = importlib.import_module(ROOT.name + ".ui.midi.map_mode")
realtime = importlib.import_module(ROOT.name + ".analyzer.midi_realtime")
thread_mod = importlib.import_module(ROOT.name + ".analyzer.midi_realtime.midi_thread")

nested = lambda: collections.defaultdict(nested)


class FakeThread:
    def __init__(self):
        self.data, self.data_controls, self.note_counts = nested(), nested(), nested()
        self.requested_devices, self.last_msg = [], None

    def cc(self, number, value, channel=1, device="Keystep"):
        self.data_controls[device][channel][number] = float(value)
        self.last_msg = thread_mod._MidiControlMessage(control=number, value=value, time=0, channel=channel,
                                                       input_name=device)

    def pad(self, note, velocity, channel=1, device="Keystep"):
        if velocity:
            self.data[device][channel][note] = float(velocity)
            counts = self.note_counts[device][channel]
            counts[note] = counts.get(note, 0) + 1
        else:
            self.data[device][channel].pop(note, None)
        self.last_msg = thread_mod._MidiNoteMessage(on=velocity > 0, note=note, velocity=velocity, time=0,
                                                    channel=channel, input_name=device)


def tick():
    analyzer = bpy.audvis.midi_realtime_analyzer
    analyzer.on_pre_frame(scene, scene.frame_current)
    fake.requested_devices = [{'custom_name': "My Keys", 'device_name': "Keystep"}]  # no real device here
    return mapping.apply(analyzer.snapshot(), analyzer, playing)


class MockLayout:
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
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    fake = FakeThread()
    analyzer = realtime.MidiRealtimeAnalyzer()
    analyzer._thread = fake
    bpy.audvis.midi_realtime_analyzer = analyzer
    scene.audvis.midi_realtime.enable = True
    item = scene.audvis.midi_realtime.inputs.add()
    item.name = "My Keys"
    playing = False

    cube = bpy.data.objects.new("Cube", bpy.data.meshes.new("Cube"))
    scene.collection.objects.link(cube)
    light = bpy.data.lights.new("Key", 'POINT')
    cube["glow"] = 0.5

    # --- parsing data paths (what right-click > Copy Full Data Path gives)
    assert mapping.parse('bpy.data.objects["Cube"].location[2]') == ('objects', 'Cube', 'location', 2)
    assert mapping.parse('bpy.data.lights["Key"].energy') == ('lights', 'Key', 'energy', -1)
    assert mapping.parse('bpy.data.scenes["Scene"].audvis.motion_master')[2] == 'audvis.motion_master'
    assert mapping.parse('bpy.data.objects["Cube"]["glow"]')[2] == '["glow"]'
    for bad in ('bpy.data.objects["Cube"].location', 'bpy.data.objects["Cube"].name',
                'bpy.data.objects["Nope"].location[0]', 'C.object.location'):
        try:
            mapping.parse(bad)
            raise AssertionError("should refuse " + bad)
        except ValueError:
            pass

    # --- a fader on a native property works while paused (no frame change)
    m = mapping.create(scene, 'cc', 7, full_path='bpy.data.objects["Cube"].location[2]')
    assert m.range_min < m.range_max
    m.range_min, m.range_max = 0, 10
    fake.cc(7, 127)
    assert tick() and abs(cube.location.z - 10) < 1e-5
    fake.cc(7, 0)
    tick()
    assert cube.location.z == 0
    bpy.context.view_layer.update()
    assert cube.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.z == 0
    assert mapping.target_label(m) == "Cube > Location Z", mapping.target_label(m)
    assert mapping.source_label(m) == "CC 7"

    # --- AudVis property, light, custom property, checkbox (pad toggle), dropdown
    mapping.create(scene, 'cc', 8, full_path='bpy.data.scenes["Scene"].audvis.motion_master')
    mapping.create(scene, 'cc', 9, full_path='bpy.data.lights["Key"].energy').range_max = 1000
    mapping.create(scene, 'cc', 10, full_path='bpy.data.objects["Cube"]["glow"]')
    toggle = mapping.create(scene, 'note', 36, full_path='bpy.data.objects["Cube"].hide_render')
    assert toggle.response == 'toggle', "notes on checkboxes default to Toggle"
    shading = mapping.create(scene, 'cc', 11, full_path='bpy.data.objects["Cube"].display_type')
    fake.cc(8, 0)
    fake.cc(9, 127)
    fake.cc(10, 127)
    fake.cc(11, 0)
    tick()
    assert scene.audvis.motion_master == 0 and light.energy == 1000 and cube["glow"] == 1.0
    assert cube.display_type == 'BOUNDS', cube.display_type
    fake.cc(11, 127)
    tick()
    assert cube.display_type == 'TEXTURED', cube.display_type
    assert not cube.hide_render
    fake.pad(36, 100)
    tick()
    assert cube.hide_render, "pad press toggles on"
    fake.pad(36, 0)
    tick()
    fake.pad(36, 90)
    tick()
    assert not cube.hide_render, "second press toggles off"

    # --- device filter (custom name from the MIDI Realtime panel) and channel
    m = scene.audvis.midi_realtime.maps[0]  # adding items moves the collection: re-fetch references
    m.device = "Other Controller"
    fake.cc(7, 64)
    tick()
    assert cube.location.z == 0, "other device knob is ignored"
    m.device = "My Keys"
    tick()
    assert abs(cube.location.z - 64 / 127 * 10) < 1e-4
    m.channel = 2
    fake.cc(7, 127)
    tick()
    assert cube.location.z < 6, "channel 1 is ignored when mapped to channel 2"
    m.channel, m.device = 0, ""

    # --- keyframed property: flagged; Record keys it while playing
    m = scene.audvis.midi_realtime.maps[0]
    cube.keyframe_insert("location", index=2, frame=1)
    assert mapping.status(m)[0] == 'KEYFRAME'
    m.record = True
    playing = True
    scene.frame_set(5)
    fake.cc(7, 32)
    tick()
    fcurve = [fc for fc in cube.animation_data.action.layers[0].strips[0].channelbag(
        cube.animation_data.action.slots[0]).fcurves if fc.data_path == 'location' and fc.array_index == 2][0] \
        if hasattr(cube.animation_data.action, "layers") else cube.animation_data.action.fcurves.find('location', index=2)
    assert any(abs(k.co.x - 5) < 1e-6 for k in fcurve.keyframe_points), "recorded a key at frame 5"
    playing = False
    m.record = False

    # --- action mappings fire once per press
    fired = []
    mapping.run_action, real_run = (lambda mm: fired.append(mm.action)), mapping.run_action
    mapping.create(scene, 'note', 40, action='release')
    fake.pad(40, 0)
    tick()
    fake.pad(40, 127)
    tick()
    tick()
    assert fired == ['release'], fired
    mapping.run_action = real_run

    # --- missing target is reported, not crashing
    gone = mapping.create(scene, 'cc', 12, full_path='bpy.data.lights["Key"].energy')
    bpy.data.lights.remove(light)
    assert mapping.status(gone)[0] == 'ERROR'
    fake.cc(12, 50)
    tick()

    # --- driver API: audvis(cc=), device filter, channel with note ranges
    fake.cc(20, 127, channel=3)
    tick()
    assert bpy.audvis.driver(cc=20) == 1.0 and bpy.audvis.driver(cc=20, ch=1) == 0.0
    assert bpy.audvis.driver(cc=20, device="My Keys") == 1.0 and bpy.audvis.driver(cc=20, device="X") == 0.0
    assert analyzer.driver(midi_control=20, device="X") == 0, "device= filters again"
    fake.pad(40, 0)  # still held from the action test
    fake.pad(45, 100, channel=1)
    tick()
    assert analyzer.driver(midi=[40, 50], ch=1) == 100 and analyzer.driver(midi=[40, 50], ch=2) == 0

    # --- learn operator: the next knob creates the mapping
    learn = mapping.AUDVIS_OT_midiMapLearn
    op = NS(full_path='bpy.data.objects["Cube"].scale[0]', map_index=-1, action="", _scene_name=scene.name,
            _start_msg=fake.last_msg, _timer=None, report=lambda *a: None, _analyzer=learn._analyzer,
            _finish=lambda ctx: None)
    before = len(scene.audvis.midi_realtime.maps)
    assert learn.modal(op, NS(), NS(type='TIMER')) == {'PASS_THROUGH'}, "waits for a new message"
    fake.cc(21, 30, channel=2)
    assert learn.modal(op, NS(), NS(type='TIMER')) == {'FINISHED'}
    new = scene.audvis.midi_realtime.maps[-1]
    assert len(scene.audvis.midi_realtime.maps) == before + 1
    assert (new.kind, new.number, new.channel, new.data_path, new.index) == ('cc', 21, 2, 'scale', 0)

    # --- Map Mode: change a value (or click it), move a knob -> mapped
    assert mapping.full_path_of(cube, "location", 2) == "bpy.data.objects['Cube'].location[2]"
    assert mapping.parse(mapping.full_path_of(cube, '["glow"]')) == ('objects', 'Cube', '["glow"]', -1)
    assert mapping.hovered_path(bpy.context) == "", "nothing hovered in background mode"
    snap = map_mode.snapshot(cube)
    assert "location[2]" in snap and "audvis.orbit.influence" in snap and '["glow"]' in snap
    cube.color[1] = .25
    assert map_mode.changed(snap, map_mode.snapshot(cube)) == ["color[1]"]

    map_mode._mode = {"scene": scene.name, "start_msg": fake.last_msg, "armed": "", "armed_label": "",
                      "last": "", "pending": set(), "ids": {}, "snapshots": {}, "stop": False}
    bpy.app.handlers.depsgraph_update_post.append(map_mode._on_depsgraph)
    map_mode._start_watching(NS(scene=scene, active_object=cube))
    mode_op = NS(_timer=None, report=lambda *a: None, _analyzer=map_mode.AUDVIS_OT_midiMapMode._analyzer,
                 _finish=lambda ctx: map_mode.AUDVIS_OT_midiMapMode._finish(mode_op, ctx))
    fake_ctx = NS(workspace=None, window_manager=NS(windows=[], event_timer_remove=lambda t: None))

    def mode_tick():
        bpy.context.view_layer.update()  # fires depsgraph_update_post like a UI edit would
        return map_mode.AUDVIS_OT_midiMapMode.modal(mode_op, fake_ctx, NS(type='TIMER', value='NOTHING'))

    m0 = scene.audvis.midi_realtime.maps[0]  # CC 7 -> location Z: its writes must not arm anything
    fake.cc(7, 100)
    tick()
    mode_tick()
    assert not map_mode._mode["armed"], "a value written by a mapping isn't 'touched'"
    map_mode.RESNAP = 60  # snapshots are throttled per ID: a change right after one waits
    cube.color[0] = .5  # the user changes a value...
    mode_tick()
    assert not map_mode._mode["armed"] and map_mode._mode["pending"], "deferred, not lost"
    map_mode.RESNAP = 0
    mode_tick()
    assert map_mode._mode["armed"] == "bpy.data.objects['Cube'].color[0]", map_mode._mode["armed"]
    assert map_mode.armed_label() == "Cube > Color R", map_mode.armed_label()
    count = len(scene.audvis.midi_realtime.maps)
    fake.cc(30, 64)  # ...and moves a knob
    mode_tick()
    maps = scene.audvis.midi_realtime.maps
    assert len(maps) == count + 1 and (maps[-1].number, maps[-1].data_path, maps[-1].index) == (30, 'color', 0)
    assert not map_mode._mode["armed"] and "CC 30 ch1 > Cube > Color R" in map_mode.last_mapped(), map_mode.last_mapped()
    fake.cc(31, 64)  # a knob with nothing armed does nothing
    mode_tick()
    assert len(scene.audvis.midi_realtime.maps) == count + 1
    map_mode.arm("bpy.data.objects['Cube'].color[0]")  # same value again: re-assign, no duplicate
    fake.pad(50, 100)
    mode_tick()
    maps = scene.audvis.midi_realtime.maps
    assert len(maps) == count + 1 and (maps[-1].kind, maps[-1].number) == ('note', 50)
    map_mode.arm("bpy.data.scenes['Scene'].audvis.midi_realtime.maps[0].range_max")
    assert not map_mode._mode["armed"], "the mapping settings themselves aren't mappable"
    helper = bpy.data.objects.new("helper", None)
    helper["audvis_motion_helper"] = True
    scene.collection.objects.link(helper)
    map_mode._watch(helper)
    helper.location.x = 3
    mode_tick()
    assert not map_mode._mode["armed"], "AudVis' own helpers are ignored"
    for state in (True, False):
        map_mode.draw_button(MockLayout(), NS())
    map_mode._mode["stop"] = True
    assert mode_tick() == {'FINISHED'} and map_mode._mode is None
    assert map_mode._on_depsgraph not in bpy.app.handlers.depsgraph_update_post
    map_mode.draw_button(MockLayout(), NS())

    # --- UI draws, timer and context menu don't fail
    for i in range(len(scene.audvis.midi_realtime.maps)):
        scene.audvis.midi_realtime.maps_index = i
        mapping.AUDVIS_PT_midiMapsNpanel.draw(NS(layout=MockLayout()), NS(scene=scene))
        lst = mapping.AUDVIS_UL_midiMaps
        lst.draw_item(NS(layout_type='DEFAULT'), None, MockLayout(), None,
                      scene.audvis.midi_realtime.maps[i], 0, None, "", i)
    mapping.draw_context_menu(NS(layout=MockLayout()), NS())
    assert mapping._tick() == mapping.TICK
    assert not mapping._reported, mapping._reported
    print("PASS: MIDI Mappings", bpy.app.version_string)
finally:
    bpy.audvis.midi_realtime_analyzer = None
    audvis.unregister()
    bpy.context.preferences.addons.remove(preferences)
