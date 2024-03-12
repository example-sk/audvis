import bpy

from .midi import AudvisMidiGeneratorsProperties
from .. import shapemodifier


class AudvisObjectArmatureGeneratorProperties(bpy.types.PropertyGroup):
    keep_old_vgroups: bpy.props.BoolProperty(name="Keep Old Vertex Groups", default=False)

    channel: bpy.props.IntProperty(name="Sound Channel", default=1, min=1, soft_max=32)
    freq_seq_type: bpy.props.EnumProperty(name="Freq Sequencing", items=[
        ("classic", "Linear", "0-50 ; 50-100 ; 100-150..."),
        ("notes", "Notes", "Music notes"),
        ("midi", "MIDI Notes", "MIDI notes from .mid files or realtime from MIDI devices"),
    ])
    midi: bpy.props.PointerProperty(name="MIDI", type=AudvisMidiGeneratorsProperties)
    note_a4_freq: bpy.props.FloatProperty(name="A4 Note Frequency", default=440.0, soft_min=432.0, soft_max=446.0)
    note_step: bpy.props.FloatProperty(name="Note Step", default=1, step=50)
    note_offset: bpy.props.IntProperty(name="Note Steps Offset", default=0)
    sound_sequence: bpy.props.StringProperty(name="Sound Sequence")
    sequence_channel: bpy.props.IntProperty(name="Sequence Channel", default=0, min=0,
                                            description="Channel number in Video Sequence Editor")

    freqrange: bpy.props.FloatProperty(name="Frequency Range Per Point", default=50, min=.01)
    freqstart: bpy.props.FloatProperty(name="Frequency Start", default=0, min=0)
    freq_step_enable: bpy.props.BoolProperty(name="Set Custom Step", default=False)
    freq_step: bpy.props.FloatProperty(name="Frequency Step", default=5.0, min=0)
    freq_step_calc: bpy.props.FloatProperty(name="Frequency Step Calculated", get=shapemodifier.calc_freq_step)
    factor: bpy.props.FloatProperty(name="Factor", default=.1, precision=4)
    add: bpy.props.FloatProperty(name="Add", default=0, precision=4)
    inset: bpy.props.BoolProperty(name="Inset", default=False)
    inset_and_extrude: bpy.props.BoolProperty(name="Extrude After Inset", default=0)
    inset_size: bpy.props.FloatProperty(name="Inset Size", default=0.01)
    armature_object: bpy.props.PointerProperty(type=bpy.types.Object, name="Armature Object")
