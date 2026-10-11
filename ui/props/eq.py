import bpy


class AudvisEQBandProperties(bpy.types.PropertyGroup):
    gain: bpy.props.FloatProperty(name="Gain", default=1, min=0, max=2,
                                  description="Multiplies the sound of every Motion FX using this band")
    mapped: bpy.props.BoolProperty(name="MIDI Mapped", default=False,
                                   description="A MIDI knob / fader controls the gain (0..2)")
    control: bpy.props.IntProperty(name="CC", default=1, min=0, max=127)
    channel: bpy.props.IntProperty(name="Channel", default=1, min=1, max=16)


classes = [
    AudvisEQBandProperties,
]
