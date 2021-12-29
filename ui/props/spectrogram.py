import bpy

from .midi import AudvisMidiGeneratorsProperties
from .. import spectrogram


class AudvisSpectrogramProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable", default=False)
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
    freqstart: bpy.props.FloatProperty(name="Frequency Start", default=0, min=0)
    freq_step_calc: bpy.props.FloatProperty(name="Frequency Step Calculated", get=spectrogram.calc_freq_step)
    sound_sequence: bpy.props.StringProperty(name="Sequence", default="")
    width: bpy.props.IntProperty(name="Image Width", default=100, soft_max=300, min=1, soft_min=10)
    height: bpy.props.IntProperty(name="Image Height", default=100, soft_max=300, min=1, soft_min=10)
    mode: bpy.props.EnumProperty(name="Mode", items=[
        ("rolling", "Rolling", "One image with selected height. Current line is always on the bottom of the image."),
        ("one-big", "One Image", "Makes one big image with height the same as the scene's frame count."
                                 " Current line is on the current frame's number,"
                                 " counted from the bottom of the image."),
        ("snapshot", "Snapshot", "Each pixel is set from the latest data")
    ], default="rolling")
    factor: bpy.props.FloatVectorProperty(name="Factor RGB", size=3, soft_min=-1, soft_max=1, default=(1, 1, 1))
    bake_path: bpy.props.StringProperty(name="Bake Path", default="//audvis-spectrogram/", subtype='DIR_PATH')
    clear_on_first_frame: bpy.props.BoolProperty(name="Clear on First Frame", default=True)
    color: bpy.props.FloatVectorProperty(
        name="Base Color",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.0, 0.0, 0.0, 1.0))
    operation: bpy.props.EnumProperty(name="Operation Type", items=[
        ('add', 'Add', 'add'),
        ('sub', 'Subtract', ''),
        ('mul', 'Multiply', ''),
        ('set', 'Set', ''),
    ])
    skip_frames: bpy.props.IntProperty(name="Skip Frames", default=0, min=0)
    # TODO: support png and targa raw, maybe other formats for baking
