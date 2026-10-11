"""Run with Blender --background --factory-startup --python-exit-code 1
--python tests/blender_compatibility_smoke.py -- <dependency-dir> [extension-zip].
Uses temporary data and never saves user preferences.
"""
import importlib
import pathlib
import sys
import tempfile
import wave
import zipfile

import bpy

ROOT = pathlib.Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index("--") + 1:]
sys.path.insert(0, args[0])
with tempfile.TemporaryDirectory(prefix="audvis-smoke-") as temporary:
    directory = pathlib.Path(temporary)
    if len(args) > 1:
        with zipfile.ZipFile(args[1]) as archive:
            archive.extractall(directory / "audvis")
        sys.path.insert(0, str(directory))
    else:
        sys.path.insert(0, str(ROOT.parent))
    audvis = importlib.import_module("audvis")
    preferences = bpy.context.preferences.addons.new()
    preferences.module = "audvis"
    audvis.register()
    try:
        # Gizmo / GizmoGroup have no is_registered; registering sets bl_rna on every class
        # UPBGE-only panels (Logic Editor) can't register in regular Blender
        spaces = bpy.types.Space.bl_rna.properties["type"].enum_items.keys()
        unregistered = [cls.__name__ for cls in audvis.classes
                        if not getattr(cls, "is_registered", "bl_rna" in cls.__dict__)
                        and getattr(cls, "bl_space_type", "VIEW_3D") in spaces]
        assert not unregistered, unregistered
        for name in ["cffi", "pygame", "sounddevice", "soundfile", "mido", "cv2"]:
            importlib.import_module(name)
        import cv2
        import numpy as np
        assert cv2.cvtColor(np.zeros((2, 2, 3), dtype=np.uint8), cv2.COLOR_BGR2GRAY).shape == (2, 2)

        from audvis.utils import action_add_fcurve, action_get_fcurves, action_remove_fcurves, get_vse_strips, get_all_vse_strips
        scene = bpy.context.scene
        assert list(get_all_vse_strips(scene)) == []
        scene.animation_data_create()
        scene.animation_data.action = bpy.data.actions.new("AudVis test")
        for name in ["note_a", "note_b", "keep"]:
            scene[name] = 0.0
            curve = action_add_fcurve(scene.animation_data.action, scene, '["' + name + '"]', -1)
            assert curve.data_path == '["' + name + '"]', curve.data_path
        action_remove_fcurves(scene.animation_data.action, '["note_')
        assert [curve.data_path for curve in action_get_fcurves(scene.animation_data.action)] == ['["keep"]']

        import mido
        from audvis.ui.midi import midi_file_baker
        midi = mido.MidiFile()
        track = mido.MidiTrack()
        midi.tracks.append(track)
        track.extend([mido.Message("note_on", note=60, velocity=90),
                      mido.Message("note_off", note=60, time=480)])
        midi_path = directory / "test.mid"
        midi.save(midi_path)
        midi_file_baker.bake(scene, str(midi_path), False, "-1")
        item = scene.audvis.midi_file.midi_files[0].tracks[0]
        curves = [curve for curve in action_get_fcurves(scene.animation_data.action)
                  if curve.data_path.startswith(item.path_from_id())]
        assert len(curves) == 1 and len(curves[0].keyframe_points) >= 3
        assert all(point.interpolation == "CONSTANT" for point in curves[0].keyframe_points)

        wav_path = directory / "test.wav"
        with wave.open(str(wav_path), "wb") as audio:
            audio.setparams((1, 2, 44100, 4410, "NONE", "not compressed"))
            audio.writeframes(b"\0\0" * 4410)
        editor = scene.sequence_editor_create()
        strip = get_vse_strips(editor).new_sound("Test", str(wav_path), 1, 1)
        assert strip in list(get_all_vse_strips(scene))
        assert hasattr(strip, "audvis")
        from audvis.ui.drivers_bake import DriverBakery
        DriverBakery().prepare(bpy.context)
        print("PASS: registration, dependencies, MIDI baking, action cleanup, audio strips, driver discovery", bpy.app.version_string)
    finally:
        audvis.unregister()
        bpy.context.preferences.addons.remove(preferences)
