# Motion FX: Cascade, Scatter, Orbit

Motion FX are algorithmic animations driven by sound (or MIDI, or plain keyframes). They live in the
**Motion FX** panel of the AudVis sidebar. Enable Motion FX in the panel header, select an object and use one
of the sub-panels. Every effect runs live while playing (also with the Realtime Analyzer / Party Mode) and
follows the sliders while the animation is paused.

Every effect has a **Presets** menu at the top - a good way to start:

| Effect  | Presets                                                                   |
|---------|---------------------------------------------------------------------------|
| Cascade | DNA Helix, Tunnel, Sunflower, Whip, Equalizer Grid                        |
| Scatter | Supernova, Disintegrate, Breathing Shards, Galaxy Shards, Bass Core / Treble Skin |
| Orbit   | Ring Collapse, Swarm, Black Hole, Planets                                 |

## Live control and your own animation

Motion FX never overwrite your objects' own animation. When an effect moves an object of yours (for example, you
pick your own collection as Orbit's *Satellites*), AudVis adds a *Copy Transforms* constraint named like
`AudVis Orbit (Center)` that follows a hidden helper in the **AudVis Motion Layer** collection. Your keyframes,
drivers and transforms stay exactly as they are: the effect only sits on top of them.

- **Influence** (top of every effect) - 1 = the effect takes over, 0 = the objects play their own animation,
  in between = a crossfade. Keyframe it to hand over at a certain bar, or map a MIDI knob to it
  (MIDI CC Control > Controls: *Influence*). Copies AudVis generated itself shrink away instead; Scatter
  pulls the pieces back together.
- **Engage / Release / Stop** - Release fades the effect out over **Fade Time** and then switches it off,
  Engage fades it (back) in, Stop cuts immediately. Fades run in real time, also while paused.
- Unchecking an effect, or Motion FX in the panel header, stops it the same way as Stop.
- The top of the **Motion FX** panel is a live strip for the whole scene: **Master** (multiplies every
  Influence), Engage / Release / Stop for everything, and one row per effect with its own Influence and buttons -
  no need to select objects while performing. Click an effect's name to select its object.
- **Overriding N objects** shows how many of your objects an effect is moving. The trash button removes the
  constraints and helpers, leaving the objects exactly as before AudVis touched them.

An object linked into several scenes is overridden in all of them - the constraint lives on the object.
There's no need to duplicate scenes to protect your animation.

## Sound settings

All effects (and attractors) share the same **Sound** settings:

- **Audio Source** - Sound (frequency range of the enabled analyzers), MIDI (a note) or Off (keyframes only)
- **Spread** - how the value is distributed over elements (copies, satellites, groups of pieces)
    - **Same for All** - one frequency range for everything
    - **Frequency Bands** - element *i* uses `Frequency Start + i * Frequency Step` (or `MIDI Note + i`)
    - **Time Delay** - element *i* gets the value from *i × Delay* frames ago - a wave travels through
- **EQ Band** - instead of Frequency Start / Range, use one of the eight bands of the
  [EQ / Macros](#eq--macros) panel; its Gain slider (or mapped MIDI knob) then scales this effect live.
  With Frequency Bands, Frequency Step still offsets each element from the band
- **Sensitivity** - multiplies the analyzer value. The effects expect values around 0..1
- **Response**
    - **Follow** - follow the loudness, smoothed by **Attack / Release**. Low Release = things float back slowly
    - **Beat Trigger** - when the value crosses the **Threshold**, fire a one-shot envelope from 0 to 1 and back:
      *Hit & Decay*, *Pulse* (smooth there and back - great for a gravity collapse that releases) or *Hold*.
      **Length** is the envelope length in frames, **Cooldown** the minimum gap between two triggers. Each
      element triggers on its own, so with Frequency Bands a kick and a hi-hat fire different elements
- **Stereo** - *Left / Right Halves*: the first half of the elements follows the Sound Channel (left), the second
  half the next channel (right). *Alternate*: every other element. For Scatter, pieces on the object's -X side
  follow the left channel, +X the right. Set **Channels Count** to 2 in the main AudVis panel

Smoothing, triggers, Time Delay and Sound → Speed need the frames to be played one after another; after a jump
(scrubbing) they start over. Render from the first frame, or [bake](#baking), if you need identical results.

## Live controls (MIDI CC)

Every effect and attractor has a **MIDI CC Control** box: click **Learn** and move a knob or fader on your
controller (MIDI Realtime must be enabled). **Controls** picks the value:

- Cascade: Reveal, Spread (× offset / spacing), Twist (× rotation)
- Scatter: Amount, Morph, Distance (×)
- Orbit: Gravity, Orbit Radius (×), Sphere Radius (×)
- Attractor: Strength

**Mode**: *Replace* (knob sets Min..Max), *Add* or *Multiply*. The knob is read directly, it isn't affected by
the global Driver Value settings.

## EQ / Macros

The **EQ / Macros** panel has eight shared frequency bands (20–60, 60–150, 150–400, 400–1k, 1k–2.5k,
2.5k–6k, 6k–12k and 12k–20k Hz), each with a live level meter and a **Gain** slider (0–2). In any Sound section,
set **EQ Band** to make that effect use the band's frequency range and multiply its sound by the band's gain.
Several effects can share one band, so a single slider rides all of them.

**Map** under a slider assigns a MIDI knob or fader (MIDI Realtime must be enabled; Esc cancels). The knob
then sets the gain from 0 to 2, and **×** clears the mapping. The window button next to **Meter Sound Channel**
opens the panel in its own window, for a second screen while performing.

## Cascade

Duplicates the active object. **Layout**:

- **Chain** - each copy is the previous one moved by **Offset**, rotated by **Rotation** and scaled by **Scale**.
  The steps compound, so a small rotation gives a spiral or a helix, scale below 1 gives a tunnel
- **Phyllotaxis** - sunflower spiral (golden angle) with **Spacing**. Offset Z raises it into a cone or dome
- **Grid** - **Columns** × **Rows** × layers with **Spacing**
- **Along Curve** - spread along the first spline of a **Curve**, facing its direction. Keyframe
  **Curve Offset** to make the copies flow along it

In the non-chain layouts Rotation and Scale are applied *per copy index* (copy 10 is rotated 10 × Rotation).

- **Output** - *Objects* (separate objects, can be baked) or *Instances* (fast: Geometry Nodes instances on one
  point cloud object - use it for thousands of copies)
- **Generate / Regenerate** - creates the copies in a new collection (linked data by default). The trash button
  deletes them. The source object itself stays where it is - it is copy number 0
- **Reveal** - shows the copies one after another. Keyframe it from 0 to 1 for a build-up
- **Sound → Offset / Rotation** - sound stretches the steps / spacing. With Time Delay, a chain whips like a tail
- **Sound → Pulse** - scales each copy (not compounding)
- **Sound → Reveal** - the sound of the first copy grows the cascade. With a Beat Trigger it grows in on every hit
- **Color Gradient** - sets the Object Color of the copies. Use it with *Object Info > Color* in shaders or
  *Viewport Shading > Color > Object*. With Instances, read the `audvis_color` attribute (Attribute node,
  type *Instancer*)

## Scatter

Tears a mesh - or a Grease Pencil drawing (Blender 4.3+) - apart into pieces and puts it back together.

- **Tear Into** - Faces (every face becomes a shard), Loose Parts (every mesh island moves as one), Vertices
  (every vertex alone - faces stretch like a web). For Grease Pencil, Faces / Loose Parts tear into strokes
- **Tear Apart** - splits the mesh and keeps a copy of the original. **Restore Original** (the arrow button)
  puts it back. Changing *Tear Into* needs *Tear Apart Again*. Meshes with shape keys are not supported.
  Grease Pencil: all frames of all layers are prepared, and every frame scatters its own drawing
- **Amount** - 0 = assembled, 1 = fully scattered. Keyframe it, or let **Sound → Amount** do it
- **Direction** - Outward (from the object origin), Face Normal, Random or a fixed Vector, mixed with randomness
- **Tumble / Tumble Speed / Shrink / Turbulence** - how the pieces behave while flying
- **Orbit Speed / Orbit Tilt** - the scattered pieces circle the object's origin (inner ones faster). Amount 0
  still snaps them back together - scatter into a ring galaxy and back
- **Stagger** - pieces leave one after another, ordered by Distance (inner first), Height or randomly. With
  Frequency Bands, the order also picks the band: by default bass shatters the core and treble peels the surface
  (*Bands / Delay Steps* sets the number of groups). With Time Delay, the shattering travels through the mesh

**Morph** - pick a **Morph Target** mesh: at **Morph** 1 the pieces rebuild the *target's* shape (on its
surface), at 0 their own. On the way they scatter (**Fly While Morphing**). The pieces are scaled to cover the
target's area (**Piece Size at Target** tweaks it). Pieces are paired with places on the target along a
space-filling curve, so neighbours stay neighbours. Amount still scatters on top of the morphed shape. The target
is read from its mesh data (without modifiers) and position at the moment it changes.

The rest positions are stored in the `audvis_rest` and `audvis_piece` attributes - you can use them in
Geometry Nodes or shaders too. Like the Shape Modifier, Scatter writes mesh data for every frame: enable
*Render > Lock Interface* when rendering.

## Orbit / Gravity

The active object (an Empty works best) is the center. Satellites circle it on tilted orbits.

- **Output** - *Objects* or *Instances* (fast - 10 000 satellites play in real time)
- **Populate** - creates **Count** copies of **Satellite Object** (small ico spheres if empty). With Objects
  output you can also pick any existing collection in **Satellites**
- **Radius Min / Max, Inclination** - the size and thickness of the swarm. Inclination 90+ gives a spherical swarm
- **Speed, Kepler Speeds** - turns per second; with Kepler, outer orbits are slower like planets
- **Rotation** - Spin (random axis), Follow Orbit (face the flight direction) or None
- **Sound → Speed** - sound pushes the orbits forward (it accumulates, so it never jumps back)
- **Sound → Radius** - sound pushes satellites outward

**Gravity Sphere** - *Gravity* (0..1, keyframe it and/or drive it with *Sound → Gravity*) pulls the satellites
in, onto a sphere of **Sphere Radius** around the center:

- **Sphere Shell** - satellites spread evenly over the sphere surface - the swarm becomes a sphere of objects.
  **Shell Spin** rotates it
- **Radial** - satellites fall straight down onto the sphere
- **Core** - satellites are swallowed by the center and shrink to nothing
- **Gravity Stagger** - outer satellites arrive later
- **Show Sphere** - if the center is an Empty, it is displayed as the gravity sphere

Moving, rotating or scaling the center moves the whole system.

## Attractors

Every effect has an **Attractors** collection. Click **+** to add an Empty at the 3D cursor (or put any objects
into the collection). Select an attractor to edit it in the **Attractor** sub-panel:

- **Attract** - pull onto a sphere of **Sphere Radius** around the attractor (Strength 1 = fully on it)
- **Repel** - push away by **Push Distance**
- **Vortex** - swirl around the attractor's Z axis by **Twist** turns
- **Strength** - keyframe it, drive it by sound (**Sound → Strength**) or a MIDI knob
- **Influence Radius** - full effect inside, fading out until twice the radius. 0 = everywhere

Attractors are applied in order (by name), later ones win. To move a swarm from one center to another,
keyframe the strength of attractor A down while B goes up. Scatter: attractors move only loose pieces (scaled by
how scattered they are), so the assembled mesh stays intact.

## Baking

Cascade and Orbit with *Objects* output can be baked to keyframes (**Bake to Keyframes**) for the scene frame
range. The live effect is disabled afterwards so the keyframes play. AudVis' own copies get the keyframes
directly; your own objects never do - the bake goes onto their helpers, so their animation stays untouched and
removing the override layer brings it back. Enabling the live effect again replaces the bake. Scatter is a function of Amount and time and
doesn't need baking - keyframe *Amount* instead. Instances can't be baked.

## Scripting

The settings are in `obj.audvis.cascade`, `obj.audvis.scatter`, `obj.audvis.orbit` and `obj.audvis.attractor`;
Motion FX for the scene is `scene.audvis.motion_enable`.
