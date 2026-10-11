# Blender AudVis

AudVis is a Blender 4.2 and higher add-on (extension) helping you to build awesome audio visualizations. The main features are Real
Time Analyzer and Sequence Analyzer.

## Important links:

- **[Download](https://github.com/example-sk/audvis/releases)**
- [Direct donation on PayPal](https://www.paypal.com/donate/?business=A8HN8ADXCKJ8Y&no_recurring=0&item_name=Do+you+love+Blender+AudVis?&currency_code=EUR)
- [BlenderMarket product page](https://www.blendermarket.com/products/audvis)
- [YouTube channel](https://www.youtube.com/channel/UCiJzmdCGdjLc_fpQgZ2fEhQ)
- [blenderartists.org discussion](https://blenderartists.org/t/audvis-audio-visualization-add-on/1183964)
- [Discord](https://discord.gg/bFzVmBGg)
- [Old documentation](https://www.blendermarket.com/products/audvis/docs)

## Building for macOS

AudVis runs inside Blender; the Mac build is an installable extension ZIP.
Run `python3 build-macos.py` to build both Apple silicon and Intel packages
in `dist/`. The build downloads Python 3.11 dependency wheels for Blender
4.2 and checks the Python sources and ZIP integrity. To build just one
architecture, use `--platform macos-arm64` or `--platform macos-x64`.

In Blender 4.2 or later with Python 3.11, open **Edit > Preferences > Add-ons**,
choose **Install from Disk** from the menu, and select the ZIP for your Mac.
Runtime verification requires Blender; packaging does not require it.

For Blender 5.2.2, run `python3 build-macos.py --blender-version 5.2`.
This creates `dist/audvis-8.0.1-blender5.2-macos-arm64.zip` with Python 3.13
wheels. Official Blender 5.2 Mac builds require Apple silicon and macOS 13+
([system requirements](https://www.blender.org/download/requirements/)).
The Python 3.11 packages are restricted to Blender versions before 5.1.

The 5.2 update covers slotted action curves, MIDI baking, sequencer strips,
and compositor driver discovery.

To install a fresh build into your local Blender 5.2 for testing (replaces the
installed AudVis; restart Blender afterwards):

```sh
python3 build-macos.py --blender-version 5.2 --skip-download
/Applications/Blender.app/Contents/MacOS/Blender --command extension install-file \
    -r user_default dist/audvis-8.0.1-blender5.2-macos-arm64.zip
```

## Tests

Headless smoke tests run inside Blender (all pass in Blender 5.2.2 on Apple silicon):

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
$B --background --factory-startup --python-exit-code 1 --python tests/blender_motion_smoke.py
$B --background --factory-startup --python-exit-code 1 --python tests/blender_motion_features_smoke.py
$B --background --factory-startup --python-exit-code 1 --python tests/blender_motion_layer_smoke.py
$B --background --factory-startup --python-exit-code 1 --python tests/blender_midi_map_smoke.py
$B --background --factory-startup --python-exit-code 1 --python tests/blender_grease_pencil_smoke.py
$B --background --factory-startup --python-exit-code 1 --python tests/blender_compatibility_smoke.py -- <dependency-dir> [extension-zip]
python3 -m unittest tests.test_blender_compatibility tests.test_grease_pencil_compat tests.test_midi_map
```

## Documentation:

* [Installing python packages](doc/packages-install.md)
* [Performing Live Visuals (shortcuts, scene switching, Party Mode)](doc/performing.md)
* Analyzers:
    - [Sequence Analyzer](doc/sequence.md)
    - [Realtime Analyzer](doc/realtime.md)
    - [MIDI File](doc/midi-file.md)
    - [MIDI Realtime](doc/midi-realtime.md)
* [Driver Values](doc/driver-values.md)
* How to animate things:
    - [Using drivers](doc/drivers.md)
    - [Shape Modifier](doc/shape-modifier.md)
    - [Motion FX: Cascade, Scatter, Orbit](doc/motion.md)
    - [EQ / Macros: shared band gains, MIDI-mappable](doc/motion.md#eq--macros)
    - [Generate Armature](doc/armature.md)
    - [Generate Example Objects](doc/example-objects.md)
    - [Scripting](doc/scripting.md)
* [Spectrogram](doc/spectrogram.md)
* [Video Capture](doc/video-capture.md)
* [Bake Drivers](doc/bake-drivers.md)
* [Spread the Drivers](doc/spread-the-drivers.md)
* [UPBGE](doc/upbge.md)
