# AudVis – notes for coding agents

AudVis is a Blender add-on/extension (manifest `blender_manifest.toml`, min Blender 4.2) for live audio
visualization: sound/MIDI analyzers feed an `audvis()` driver function, plus generators, Motion FX and live
performance tools. The maintainer develops on an Apple-silicon Mac with **Blender 5.2.2** at
`/Applications/Blender.app` and uses both Claude Code and Codex on this repo. Keep this file current for both.

## Layout

- `__init__.py` – add-on entry. `register2()` registers `ui.classes + scripting.classes` and **silently swallows
  `register_class` errors**, so a broken class just disappears. `tests/blender_compatibility_smoke.py` catches that.
- `audvis_class.py` – the `AudVis` singleton (`bpy.audvis`). `driver(low, high, ch, **kw)` is the driver function;
  it reads `bpy.context.scene`, not a scene argument. `update_data` runs on `frame_change_pre`.
  `midi_cc(control, channel)` → 0..1 or None. `get_midi_realtime_analyzer(scene)` can return None.
- `analyzer/` – analyzers. `analyzer/motion/` is the Motion FX engine (`MotionEngine(driver, cc_reader)`);
  `audio.py` holds the shared sound sampling, triggers, MIDI CC helpers and the EQ band edges/gain (`EQ_EDGES`,
  `eq_gain`, `eq_band`). Keep it free of `bpy` imports where possible – tests drive it with `SimpleNamespace` props.
- `ui/` – panels and operators, one module per feature (`motion.py`, `eq.py`, `partymode/`, `midi/`…).
  Sidebar panels subclass `AudVisButtonsPanel_Npanel` (`ui/buttonspanel.py`). Add new modules to the import list,
  `classes` and `register()/unregister()` in `ui/__init__.py`.
- `ui/props/` – PropertyGroups. A group used by `AudvisSceneProperties` must be listed **before** it in
  `ui/props/__init__.py`. Window-level flags live in `AudvisWindowProperties` (`ui/__init__.py`).
- Compat helpers: `utils.py` (VSE strips, slotted-action f-curves, `call_ops_override`), `grease_pencil_compat.py`,
  `switchscenes.py` (`switch_window_scene` – the one way to switch scenes and restart playback).
- `doc/*.md` – user docs, linked from `README.md`. Update them with every user-facing change.

## Conventions and gotchas

- **Never write the transform of the user's own objects.** Motion FX go through `analyzer/motion/layer.py`:
  user objects get a Copy Transforms constraint to a hidden helper (collection "AudVis Motion Layer"); only the
  helper and the constraint influence are written. Objects with `INDEX_KEY` (AudVis-generated copies) are placed
  directly. Bakes key the helpers, never the user's action. A `frame_change_pre` write to an animated property is
  overwritten by its f-curve anyway - constraints evaluate after animation, in viewport and final render.
- Effect strength = `influence` (keyframable, MIDI CC target `influence`) x Engage/Release gate (`engine.gates`,
  wall-clock, runtime only) x `scene.audvis.motion_master`. Switching an effect off must release its layer
  (`_on_disable` in `ui/motion.py`).
- Dynamic enum items (e.g. `CC_TARGETS`) are saved by position - only append.
- Adding to a `CollectionProperty` can move its items in memory: re-fetch item references after `.add()`.
- MIDI: one subprocess per device (`analyzer/midi_realtime/midi_realtime_proxy.py`, mido + pygame backend) feeds
  `MidiThread`; it replaces (never mutates) `data` / `data_controls` / `note_counts`, so readers just take the
  reference. `MidiRealtimeAnalyzer.snapshot()` reads them while paused; `device_key()` maps panel names to hardware.
- MIDI Mappings (`ui/midi/mapping.py`, math in `analyzer/midi_map.py` without bpy): mappings live in
  `scene.audvis.midi_realtime.maps`, are applied by a 60 Hz timer (not frame handlers) from every scene, and are
  created by Map Mode (`ui/midi/map_mode.py`: hovered button via `context.property` under a region
  `temp_override`, or a changed value found by diffing RNA snapshots of depsgraph-updated IDs) or right-click >
  AudVis: MIDI Learn (`UI_MT_button_context_menu`, same `context.property` lookup). Prefer
  this over new one-off "Learn" buttons; Motion FX CC Control and EQ Map predate it.

- Motion FX props get an automatic `update=motion.refresh` via `_refresh_on_change` in `ui/props/motion.py`;
  add internal/state props to its `skip` set.
- Don't write RNA properties from timers or every frame just for display (it dirties the file and triggers
  depsgraph updates). Keep transient UI state such as meter levels in module-level dicts (see `ui/eq.py`).
- Modal operators: store names, not RNA references (scenes/objects may be deleted), and handle the MIDI analyzer
  becoming None / MIDI Realtime being switched off mid-modal – cancel cleanly and reset any `is_learning` flag.
- MIDI thread messages: `msg.channel` is 1-based; CC messages have `.control`.
- Blender 5.2: `GizmoGroup`/`Gizmo` classes have no `is_registered`; `LOGIC_EDITOR` exists only in UPBGE, so
  `AUDVIS_PT_Bge` never registers in regular Blender (expected). `SoundSequence` became `SoundStrip`.
- Match the surrounding style: short docstrings, `bpy.props` annotations, descriptions on user-facing props.

## Test

All of these must pass before committing (headless, ~1 min total):

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
$B --background --factory-startup --python-exit-code 1 --python tests/blender_motion_smoke.py
$B --background --factory-startup --python-exit-code 1 --python tests/blender_motion_features_smoke.py
$B --background --factory-startup --python-exit-code 1 --python tests/blender_motion_layer_smoke.py
$B --background --factory-startup --python-exit-code 1 --python tests/blender_midi_map_smoke.py
$B --background --factory-startup --python-exit-code 1 --python tests/blender_grease_pencil_smoke.py
$B --background --factory-startup --python-exit-code 1 --python tests/blender_compatibility_smoke.py -- "$(mktemp -d)"
python3 -m unittest tests.test_blender_compatibility tests.test_grease_pencil_compat tests.test_midi_map
```

Headless tests can't exercise drawing, windows or real MIDI hardware – say so when reporting UI work.

## Build and install locally

```sh
python3 build-macos.py --blender-version 5.2 --skip-download   # dist/audvis-<ver>-blender5.2-macos-arm64.zip
$B --command extension install-file -r user_default dist/audvis-8.0.1-blender5.2-macos-arm64.zip
```

`--skip-download` uses the wheels cached in `wheels/blender52/macos-arm64/`. Without `--blender-version 5.2` it
builds the Blender 4.2–5.0 (Python 3.11) packages. `dist/` and `wheels/` are git-ignored.

## Git

- Work on `main` unless asked otherwise; commit only when asked.
- Commit messages: a short summary line plus bullet points of what changed – not a chat transcript.
