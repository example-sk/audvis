import bpy

from .midi import AudvisMidiGeneratorsProperties
from .. import shapemodifier
from ...analyzer.shapemodifier import create_shapemodifier_vertgroup


class AudvisObjectShapemodifierProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable", default=False)
    order: bpy.props.EnumProperty(name="Order", items=shapemodifier.order_enum)
    channel: bpy.props.IntProperty(name="Sound Channel", default=1, min=1, soft_max=32)
    random_seed: bpy.props.IntProperty(name="Randomize Seed", default=1)
    freq_seq_type: bpy.props.EnumProperty(name="Freq Sequencing", items=[
        ("classic", "Linear", "0-50 ; 50-100 ; 100-150..."),
        ("notes", "Notes", "Music notes"),
        ("midi", "MIDI Notes", "MIDI notes (limited to 127 points)"),
    ])
    note_a4_freq: bpy.props.FloatProperty(name="A4 Note Frequency", default=440.0, soft_min=432.0, soft_max=446.0)
    note_step: bpy.props.FloatProperty(name="Note Step", default=1, step=50)
    note_offset: bpy.props.IntProperty(name="Note Steps Offset", default=0)

    midi: bpy.props.PointerProperty(name="MIDI", type=AudvisMidiGeneratorsProperties)

    freqrange: bpy.props.FloatProperty(name="Frequency Range Per Point", default=50, min=.01)
    freqstart: bpy.props.FloatProperty(name="Frequency Start", default=0, min=0)
    freq_step_enable: bpy.props.BoolProperty(name="Set Custom Step", default=False)
    freq_step: bpy.props.FloatProperty(name="Frequency Step", default=5.0, min=0)
    freq_step_calc: bpy.props.FloatProperty(name="Frequency Step Calculated", get=shapemodifier.calc_freq_step)
    animtype: bpy.props.EnumProperty(name="Animation Type", items=shapemodifier.animation_type_enum)
    additive: bpy.props.EnumProperty(name="Additive", default="off", items=[
        ('off', 'Off', ''),
        ('on', 'On', ''),
        ('sin', 'Sine from -1 to 1', ''),
        ('sin2', 'Sine from 0 to 1', ''),
        ('mod', 'Modulo', ''),
    ])
    additive_modulus: bpy.props.FloatProperty(name="Modulus", default=1.0)
    additive_phase_multiplier: bpy.props.FloatProperty(name="Phase Multiplier", default=1.0)
    additive_phase_offset: bpy.props.FloatProperty(name="Phase Offset", default=0.0)
    factor: bpy.props.FloatProperty(name="Factor", default=.1, precision=4)
    add: bpy.props.FloatProperty(name="Add", default=0, precision=4)
    use_vertexgroup: bpy.props.BoolProperty(name="Use Vertex Group", default=False,
                                            update=create_shapemodifier_vertgroup)
    gpencil_layer: bpy.props.StringProperty(name="Layer", default="", update=shapemodifier.gpencil_layer_changed)
    gpencil_layer_changed: bpy.props.BoolProperty(name="GPencil Layer Value Changed", default=False)
    vector: bpy.props.FloatVectorProperty(name="Vector", default=[0, 0, 1], subtype='TRANSLATION')
    uv_vector: bpy.props.FloatVectorProperty(name="UV", default=[1, 0], size=2)
    vertcolor_color: bpy.props.FloatVectorProperty(name="Vertex Color", default=[1, 1, 1], size=3, subtype='COLOR')
    operation: bpy.props.EnumProperty(name="Operation Type", items=[
        ('add', 'Add', 'add'),
        ('set', 'Set', 'set'),
    ])
    track_object: bpy.props.PointerProperty(type=bpy.types.Object, name="Target")
    is_baking: bpy.props.BoolProperty(name="Enable", default=False)
    sound_sequence: bpy.props.StringProperty(name="Sequence", default="")
    sequence_channel: bpy.props.IntProperty(name="Sequence Channel", default=0, min=0,
                                            description="Channel number in Video Sequence Editor")
