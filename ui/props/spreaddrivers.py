import bpy
from .midi import AudvisMidiGeneratorsProperties

class AudvisSceneSpreaddriversProperties(bpy.types.PropertyGroup):
    iteration: bpy.props.IntProperty(name="Iteration", default=0, soft_min=0)
    factor: bpy.props.FloatProperty(name="Factor", default=1)
    add: bpy.props.FloatProperty(name="Add Value", default=0)
    freqrange: bpy.props.FloatProperty(name="Frequency Range Per Iteration", default=50)
    freqstart: bpy.props.FloatProperty(name="Frequency Start", default=0, min=0)
    additive: bpy.props.BoolProperty(name="Additive", default=False)

    freq_step_enable: bpy.props.BoolProperty(name="Set Custom Step", default=False)
    freq_step: bpy.props.FloatProperty(name="Frequency Step ", default=5.0, soft_min=0, soft_max=1000,
                                       description="If set to 5, objects will use"
                                                   " frequencies 0-50, 5-55, 10-60...")
    channel: bpy.props.IntProperty(name="Sound Channel", default=1, min=1, soft_max=32)
    sound_sequence: bpy.props.StringProperty(name="Sequence")
    freq_seq_type: bpy.props.EnumProperty(name="Freq Sequencing", items=[
        ("classic", "Linear", "0-50 ; 50-100 ; 100-150..."),
        ("notes", "Notes", "Music notes"),
        ("midi", "MIDI Notes", "MIDI notes (limited to 127 points)"),
    ])
    note_a4_freq: bpy.props.FloatProperty(name="A4 Note Frequency", default=440.0, soft_min=432.0, soft_max=446.0)
    note_step: bpy.props.FloatProperty(name="Note Step", default=1, step=50)
    note_offset: bpy.props.IntProperty(name="Note Steps Offset", default=0)
    midi: bpy.props.PointerProperty(name="MIDI", type=AudvisMidiGeneratorsProperties)
    expression: bpy.props.StringProperty(name="Expression", default="audvis()")
