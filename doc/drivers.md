# Drivers

You can animate many, many things by writing your own drivers. Just right click on any numeric value, for example
object's Location X, and click "Add Driver". Then write any expression.

Simplest formula looks like this: `audvis(100, 200)` - this will animate your property by sound frequencies 100Hz -
200Hz.

## Python driver expressions

You want to read the manual [here](https://docs.blender.org/manual/en/latest/animation/drivers/drivers_panel.html),
[here](https://docs.blender.org/manual/en/latest/animation/drivers/introduction.html)
and [especially here](https://docs.blender.org/manual/en/latest/animation/drivers/drivers_panel.html#drivers-simple-expressions)
.

Here are some simple expressions to show what you probably want to do:

- `audvis(100, 200) * 10 + 100`
- `3 - audvis(100, 200) / 15`
- `clamp(audvis(100, 200) / 3, 0, 3)`

## Expressions for Realtime and Sequence analyzers:

- **seq** - `audvis(100, 200, seq="MyGreatSong.mp3")` - only react to MyGreatSong.mp3
- **ch** - `audvis(100, 200, ch=2)` - channel. By default, only one channel is parsed, so if you want to use more of
  them, you need to increase the value of `Channels Count` property in the main AudVis panel
- **seq** and **ch** can be combined - `audvis(100, 200, seq="MyGreatSong.mp3", ch=2)`

## Expressions for MIDI File and MIDI Realtime analyzers:

- **midi** - `audvis(midi=1)` - note 1. This parameters is needed if you want to use any midi
- **device** - `audvis(midi=1, device="MIDI Device 1")` - name of the device from the MIDI Realtime panel
- **ch** - `audvis(midi=1, ch="1")` - midi channel
- **file** - `audvis(midi=3, file='MyGreatSong.mid')` - file name from the MIDI File panel
- **track** - `audvis(midi=3, file='MyGreatSong.mid', track='Track 1')` - track from the file. If your tracks in the
  MIDI are not named, they will get names like "Track 1"
- you can combine **device** + **ch**, or **file** + **track** + **ch**, but **device** + **file** makes absolutely no
  sense.

## Some ideas what to animate with drivers:

- object's basic properties like location, rotation, scale
- shape key value
- array modifier's Count property
- `Object -> Viewport Display -> Color` and use it inside shading nodes`
- armature bones' properties - rotation and/or scale or event Bone Constraints
- light color / power / radius...
- camera focal length
- almost any nodes in geometry nodes, shading, compositing...
- depth of field settings
- just experiment! Explore all the possibilities (impossible) and have fun