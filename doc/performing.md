# Performing Live Visuals

This guide is for using AudVis on stage: Blender reacts to live audio, and you switch between scenes while the music
plays. It also lists the keyboard shortcuts you'll reach for during a set.

Read first: [Realtime Analyzer](./realtime.md) and [Using drivers](./drivers.md)

## Keyboard shortcuts

AudVis itself adds only one shortcut. Everything else is a standard Blender shortcut (default keymap), or a custom one
somebody added. See [Your own shortcuts](#your-own-shortcuts) to find and make those.

### AudVis

| Shortcut | What it does |
|---|---|
| **Esc** | Leave Party Mode (in the Party Mode 3D view) |
| **Esc** | Cancel a running bake (drivers, spectrogram, Shape Modifier) |
| **Click** the close button, bottom right | Leave Party Mode. The button only shows while playback is stopped |

### Playback

AudVis only reacts while the animation is playing. If nothing moves, check that playback is running.

| Shortcut | What it does |
|---|---|
| **Space** | Play / pause |
| **Shift Ctrl Space** | Play backwards |
| **Esc** | Stop playback and jump back to where it started (outside Party Mode) |
| **Shift ←** / **Shift →** | Jump to the first / last frame |
| **←** / **→** | Step one frame back / forward |
| **↑** / **↓** | Jump to the next / previous keyframe |

If Space opens a menu instead of playing, change **Preferences > Keymap > Spacebar Action** to *Play*.

### Viewport and screen

| Shortcut | What it does |
|---|---|
| **N** | Show / hide the sidebar, where the **AudVis** tab lives |
| **T** | Show / hide the toolbar |
| **Z** | Shading pie menu: Wireframe, Solid, Material, Rendered |
| **Alt Z** | Toggle X-Ray |
| **Shift Alt Z** | Toggle overlays (grid, outlines, gizmos) |
| **Numpad 0** | Look through the scene camera |
| **Home** | Frame everything in view |
| **Ctrl Space** | Maximize the area under the mouse (press again to restore) |
| **Ctrl Alt Space** | Maximize the area and hide all its UI (press again to restore) |
| **Ctrl Page Up** / **Ctrl Page Down** | Previous / next workspace |
| **F3** | Search for any command by name, for example "Enter Party Mode" or "Switch Scene" |
| **F12** | Render the current frame |

On a Mac laptop without a numpad, turn on **Preferences > Input > Emulate Numpad** so the number row works as a numpad.

## Your own shortcuts

If a shortcut does something that isn't listed above, someone added it. To list them, open **Preferences > Keymap**,
type `audvis` in the search field, and switch the search to **Name** if needed. Custom entries are in the **User**
section at the bottom, or are marked as modified.

To give any AudVis button a shortcut:

1. Right-click the button, for example **Enter Party Mode** or a scene in the **Scenes** grid.
2. Choose **Assign Shortcut** and press the keys.
3. Save the preferences if auto-save is off (**Preferences > ☰ > Save Preferences**).

Scene buttons keep the scene name, so you can map keys to scenes, for example **1**–**9** to your first nine scenes.
Choose keys that don't clash with keys you use while performing. Because shortcuts are stored in your Blender
preferences, not in the .blend file, export them (**Preferences > Keymap > Export**) and import them on the show
computer.

## Before the gig

1. **Audio input.** On macOS, route the music through a loopback driver such as
   [BlackHole](https://github.com/ExistentialAudio/BlackHole), or use the mixer's line-in. Pick it in
   **AudVis > Real Time Analyzer > Input Device** and enable the panel header checkbox. If the device doesn't show up,
   click **Reconnect and reload device list**.
2. **Auto Run Python Scripts.** AudVis drivers are Python expressions. Blender doesn't run them in a file it doesn't
   trust, so enable **Preferences > Save & Load > Auto Run Python Scripts**, or click **Allow Execution** when the file
   opens. Otherwise nothing will react.
3. **Frame rate.** Watch the FPS counter in the viewport (**Overlays > Statistics**) while music plays. If it drops,
   lower **Subframes**, simplify heavy scenes, or use Solid/Material shading instead of Rendered.
4. **Sync Mode.** In the AudVis tab, set **Sync Mode** to *Frame Dropping* so a slow frame doesn't make the visuals
   lag behind the music.
5. **Display.** Connect the projector and arrange the displays before you open Blender. Moving windows between screens
   in the middle of a set is awkward.
6. **Save** your work, and keep a copy of the .blend on the show computer.

## During the set

### Switching scenes

Make one scene per look. Scenes can share objects, or each can have its own. Then switch between them live:

- **Scenes grid** (AudVis tab at the top of the sidebar): click a scene. It starts from its first frame and plays
  right away. The active scene's button is highlighted.
- **Auto Switch Scenes** (Real Time Analyzer panel): when a playing scene reaches its last frame, the next scene in the
  list starts. After the last scene it goes back to the first. Avoid very short scenes, or the switching will look
  hectic.
- **Your own keys:** assign shortcuts to the scene buttons (see [Your own shortcuts](#your-own-shortcuts)).

Scene switches don't create undo steps, so clicking scenes stays smooth even in heavy files.

### Party Mode

Party Mode shows the 3D view full screen with no UI, which is what you want on the projector.

1. In the **AudVis > Party Mode** panel, choose the **Shading** (Rendered looks best; Solid or Wireframe are faster)
   and, if you like, **Hide Mouse Pointer**.
2. Click **Enter Party Mode**, or use **Render > Enter Party Mode** from the top menu. Playback starts on its own.
3. Press **Esc** to leave.

Party Mode adds a temporary `audvis-party` workspace and deletes it again on exit.

### Live tweaks

- Keep the sidebar (**N**) open on the AudVis tab of your control screen to adjust Driver Values (multiplier, noise,
  fade-out) during the set. See [Driver Values](./driver-values.md).
- Use **MIDI Realtime** to drive values from a controller's knobs and pads: right-click any value > **AudVis:
  MIDI Learn**, move a knob - or switch on **Map Mode** and map one value after another. Map pads to scene switching and Motion FX Engage / Release / Stop. See
  [MIDI Mappings](./midi-realtime.md#midi-mappings-map-knobs-faders-and-pads).
- Bring Motion FX in and out with the live strip at the top of the **Motion FX** panel: **Master**, and
  Engage / Release / Stop per effect or for everything. Your scene's own animation keeps playing underneath. See
  [Live control](./motion.md#live-control-and-your-own-animation).
- Ride the Motion FX with the **EQ / Macros** panel: eight band gain sliders, each mappable to a knob or fader with
  **Map**. Open it in its own window (the window button in the panel) and put it on your control screen. See
  [EQ / Macros](./motion.md#eq--macros).
- If the audio input stops responding, click **Reconnect and reload device list**, or toggle the Real Time Analyzer checkbox off and on. If that doesn't help,
  click **Reload AudVis** at the bottom of the main AudVis panel.

## Troubleshooting

| Problem | Fix |
|---|---|
| Nothing moves | Press **Space**: AudVis only updates during playback. Check the Real Time Analyzer checkbox and input device. |
| Drivers show errors or stay at 0 | Allow Python scripts (see [Before the gig](#before-the-gig)). |
| Visuals lag behind the music | Set **Sync Mode** to *Frame Dropping*, lower **Subframes**, or use lighter shading. |
| Party Mode won't close | Press **Esc** with the mouse over the full-screen view, or stop playback and click the close button in the bottom right. |
| A scene button does nothing | The scene may have been renamed or deleted. Check the warning in the status bar. |
