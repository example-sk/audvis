import bpy

from . import (
    spectrogram,
    animationnodes,
    valuesaud,
    party,
    midi,
    spreaddrivers,
    daw_arrangement,
    realtimeprops,
)
from .. import (
    values,
    global_settings,
    realtime,
    generator,
)
from ...analyzer.video import webcam_toggle_callback

switchscenes = global_settings.GlobalSettings('switchscenes_enable', default=False)
realtime_device = global_settings.GlobalSettings('realtime_device')
realtime_enable = global_settings.GlobalSettings('realtime_enable', default=False)


class AudvisSceneProperties(bpy.types.PropertyGroup):

    def get_sound_sequences(self, context):
        res = [("", "---", "")]
        if context.scene.sequence_editor is None:
            return res
        for seq in context.scene.sequence_editor.sequences_all:
            if seq.type == 'SOUND':
                res.append((seq.name, seq.name, seq.name))
        return res

    # party mode
    party: bpy.props.PointerProperty(type=party.AudvisPartyProperties)

    midi_realtime: bpy.props.PointerProperty(type=midi.AudvisMidiProperties)
    midi_file: bpy.props.PointerProperty(type=midi.AudvisMidiFilesProperties)

    # daw arrangement
    daw_arrangement: bpy.props.PointerProperty(type=daw_arrangement.AudvisDawArrangement)

    # channels
    channels: bpy.props.IntProperty(name="Channels Count", default=1, min=1, soft_max=32,
                                    description="Number of channels to perform the analysis. Useful with stereo sound.")
    default_channel_sound: bpy.props.IntProperty(name="Default Sound Channel", default=1, min=1)
    default_channel_midi: bpy.props.EnumProperty(name="Default MIDI Channel",
                                                 default='all',
                                                 items=[('all', 'All', '')] + [
                                                     (str(i + 1), str(i + 1), "")
                                                     for i in range(16)
                                                 ])

    # spectrogram
    spectrogram: bpy.props.PointerProperty(type=spectrogram.AudvisSpectrogramProperties)
    spectrogram_meta: bpy.props.PointerProperty(type=spectrogram.AudvisSpectrogramMetaProperties)
    spectrograms: bpy.props.CollectionProperty(type=spectrogram.AudvisSpectrogramProperties)

    # animation nodes
    animation_nodes: bpy.props.PointerProperty(type=animationnodes.AudvisAnimationnodesProperties)

    # spread drivers
    spreaddrivers: bpy.props.PointerProperty(type=spreaddrivers.AudvisSceneSpreaddriversProperties)

    # nonstop baking (Bake Drivers)
    nonstop_baking_collection: bpy.props.PointerProperty(name="Nonstop Baking Collection", type=bpy.types.Collection,
                                                         description="Inserts keyframes all the time.")
    nonstop_baking_editexpressions: bpy.props.BoolProperty(name="Edit Driver Expressions Here",
                                                           description="Show all objects' inside selected collection"
                                                                       " drivers expressions."
                                                                       " This is helpful because the drivers are hidden"
                                                                       " in the input by the keyframes.")

    # values
    value_normalize: bpy.props.EnumProperty(name="Normalize Values", description="", items=[
        ("none", "No", "Values are just virtual numbers"),
        ("ortho", "Ortho", "Numpy's normalization 'ortho'." +
         " See https://docs.scipy.org/doc/numpy/reference/routines.fft.html#normalization"),
        ("max", "Clamp", "Divide all values by the highest value, so no value will exceed given value."),
    ])
    value_normalize_clamp_to: bpy.props.FloatProperty(name="Clamp to", default=100.0, min=.001,
                                                      description="All values will be under this value")
    value_logarithm: bpy.props.BoolProperty(name="Logarithm", default=False, description="log(value+1)")
    value_factor: bpy.props.FloatProperty(name="Factor", default=1.0, min=.001,
                                          description="Multiply value by this number")
    value_max: bpy.props.FloatProperty(name="Max", default=100.0, soft_max=100, min=0)
    value_add: bpy.props.FloatProperty(name="Add (after max)", default=0, soft_min=0)
    value_highpass_freq: bpy.props.IntProperty(name="Highpass Frequency", default=1000, min=0, soft_max=10000)
    value_highpass_factor: bpy.props.FloatProperty(name="Highpass Strength", default=0, min=0, max=1)
    value_noise: bpy.props.FloatProperty(name="Add Noise", default=0, min=0, step=.5, precision=3)
    value_fadeout_type: bpy.props.EnumProperty(name="Fade Out Type", items=[
        ('off', "Off", ""),
        ('linear', "Linear", ""),
        ('exponential', "Exponential", ""),
        ('natural', "Natural (obsolete)", ""),
        ('natural2', "Natural", ""),
    ])
    value_additive_type: bpy.props.EnumProperty(name="Additive Type", default="raw", items=[
        ('off', "Off", ""),
        ('raw', "Raw", ""),
        ('use_fadeout', "Use Fadeout", ""),
    ])
    value_additive_reset: bpy.props.BoolProperty(name="Reset Additive on First Frame", default=True)
    value_fadeout_speed: bpy.props.FloatProperty(name="Fade Out Speed", min=0, max=1, default=.1)

    # aud.Sound magic
    value_aud: bpy.props.PointerProperty(type=valuesaud.AudvisValuesAudProperties)

    # general
    subframes: bpy.props.IntProperty(name="Subframes", default=0, min=0, max=20,
                                     description="Use with caution. If you don't need it, don't use it")
    sample: bpy.props.IntProperty(name="Sample Size (seconds/1000)", default=100, min=1, step=1, soft_max=1000,
                                  description="How long chunk of sound to analyze. Affects overall impression."
                                              " Just play with this value during animation")
    sample_calc: bpy.props.FloatProperty(get=values.get_sample_calc)

    # realtime
    realtime_enable: bpy.props.BoolProperty(name="Realtime Audio Visualizer", get=realtime_enable.getter(),
                                            set=realtime_enable.setter())
    realtime_device: bpy.props.EnumProperty(name="Input Device", items=realtime.input_device_options,
                                            set=realtime_device.setter(), get=realtime_device.getter())
    realtime_switchscenes: bpy.props.BoolProperty(name="Auto Switch Scenes", default=False, get=switchscenes.getter(),
                                                  set=switchscenes.setter())
    realtime_save_format: bpy.props.EnumProperty(name="Save Format", items=realtime.recording.get_available_formats)
    realtime_loadassequence: bpy.props.BoolProperty(name="Load as Sequence", default=True)
    realtime_save_pack: bpy.props.BoolProperty(name=" - Pack after Load", default=True)

    realtime_multi_enable: bpy.props.BoolProperty(name="Multiple Realtime Sources")
    realtime_multi_list: bpy.props.CollectionProperty(type=realtimeprops.AudvisRealtimeProperties)
    realtime_multi_index: bpy.props.IntProperty(default=0)

    # video
    video_webcam_enable: bpy.props.BoolProperty(name="AudVis Video", update=webcam_toggle_callback)
    video_webcam_index: bpy.props.IntProperty(name="Camera index")
    video_image: bpy.props.PointerProperty(name="Output Image", type=bpy.types.Image)
    video_image_flip_horizontal: bpy.props.BoolProperty(name="Flip Horizontal")
    video_tmppath: bpy.props.StringProperty(name="Temp Path", default="", subtype="DIR_PATH")
    video_resize: bpy.props.BoolProperty(name="Resize Image")
    video_resize_relative: bpy.props.BoolProperty(name="Relative resize", default=False)
    video_resize_ratio: bpy.props.FloatProperty(name="Ratio", default=0.5, min=0.0, soft_max=1.0)
    video_width: bpy.props.IntProperty(name="Width", default=640, min=1)
    video_height: bpy.props.IntProperty(name="Height", default=480, min=1)
    video_contour_enable: bpy.props.BoolProperty(name="Contour Object", default=False)
    video_contour_chain_approx: bpy.props.EnumProperty(name="Chain Approx", items=[
        ("CHAIN_APPROX_NONE", "None", ""),
        ("CHAIN_APPROX_SIMPLE", "Simple", ""),
        ("CHAIN_APPROX_TC89_KCOS", "TC89_KCOS", ""),
        ("CHAIN_APPROX_TC89_L1", "TC89_L1", ""),
    ])
    video_contour_simplify: bpy.props.FloatProperty(name="Simplify", default=2, min=0)
    video_contour_threshold: bpy.props.IntProperty(name="Threshold", default=150, min=0, max=255)
    video_contour_object_type: bpy.props.EnumProperty(name="Object Type", items=[
        ("GPENCIL", "GPencil", ""),
        ("CURVE", "Curve", ""),
        ("MESH", "Mesh", ""),
    ])
    video_contour_object: bpy.props.PointerProperty(name="Object to Copy", type=bpy.types.Object)
    video_contour_min_points_per_stroke: bpy.props.IntProperty(name="Min Points per Stroke", default=15, min=0)
    video_contour_size: bpy.props.FloatProperty(name="Size", default=5.0)

    # sequence
    sequence_enable: bpy.props.BoolProperty(name="Enable Sequences Visualizer", default=False)
    sequence_list_index: bpy.props.IntProperty(name="List Index")
    sequence_offset: bpy.props.IntProperty(name="Audio Offset (seconds/1000)", default=0, soft_min=-1000,
                                           soft_max=1000,
                                           step=1)
    sequence_chunks: bpy.props.BoolProperty(name="Smaller Chunks", default=True,
                                            description="Loading a large sound into memory will cause massive"
                                                        " memory consumption.\nOn the other hand, cutting it into"
                                                        " smaller chunks can cause minor lags while playing"
                                                        " animation in Blender (not in the rendered animation)")

    # shape modifier
    shapemodifier_enable: bpy.props.BoolProperty(name="Enable AudVis Shape Modifier")

    # example
    example_channel: bpy.props.IntProperty(name="Sound Channel", default=1, min=1, soft_max=32)
    example_xcount: bpy.props.IntProperty(name="X Count", default=10, min=1, soft_max=500,
                                          description="Number of rows")
    example_ycount: bpy.props.IntProperty(name="Y Count", default=10, min=1, soft_max=500,
                                          description="Number of cols")
    example_zcount: bpy.props.IntProperty(name="Z Count", default=1, min=1, soft_max=500,
                                          description="Number of layers")

    example_driver_objectdrivers: bpy.props.BoolProperty(name="Modify Existing Drivers", default=False,
                                                         description='Find all drivers in modifiers etc,'
                                                                     ' and replaces "audvis()"\n'
                                                                     'with "audvis(lowHZ, highHZ)"'
                                                                     ' in the driver\'s expression')  # modifiers...

    example_freq_seq_type: bpy.props.EnumProperty(name="Freq Sequencing", items=[
        ("classic", "Linear", "0-50 ; 50-100 ; 100-150..."),
        ("notes", "Notes", "Music notes"),
    ])
    example_note_a4_freq: bpy.props.FloatProperty(name="A4 Note Frequency", default=440.0, soft_min=432.0,
                                                  soft_max=446.0)
    example_note_step: bpy.props.FloatProperty(name="Note Step", default=1, step=50)
    example_note_offset: bpy.props.IntProperty(name="Note Steps Offset", default=0)

    example_driver_scalex: bpy.props.BoolProperty(name="Animate Scale X", default=False)
    example_driver_scaley: bpy.props.BoolProperty(name="Animate Scale Y", default=False)
    example_driver_scalez: bpy.props.BoolProperty(name="Animate Scale Z", default=True)

    example_driver_locx: bpy.props.BoolProperty(name="Animate Location X", default=False)
    example_driver_locy: bpy.props.BoolProperty(name="Animate Location Y", default=False)
    example_driver_locz: bpy.props.BoolProperty(name="Animate Location Z", default=False)

    example_driver_rotx: bpy.props.BoolProperty(name="Animate Rotation X", default=False)
    example_driver_roty: bpy.props.BoolProperty(name="Animate Rotation Y", default=False)
    example_driver_rotz: bpy.props.BoolProperty(name="Animate Rotation Z", default=False)

    example_material: bpy.props.EnumProperty(name="Material Color", default="None", items=[
        ("None", "Nope", "Nope"),
        ("One", "One for All", "One material for all objects"),
        ("Many", "Many", "Each object will have it's own material. Warning! This will duplicate data for each object"),
        ("Copy+Modify", "Copy and Modify", "You will create a material, add drivers for"
                                           " the properties by your selection, and I will replace string audvis() to"
                                           " something better."),
    ])
    example_material_basecolor: bpy.props.FloatVectorProperty(
        name="Base Color",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 0.0, 0.0, 1.0)
    )
    example_material_channel: bpy.props.EnumProperty(name="Material Color Channel", default="1", items=[
        ("0", "Red", ""),
        ("1", "Green", ""),
        ("2", "Blue", ""),
        ("3", "Alpha", ""),
        ("gray", "Gray Scale", "Same driver on red, green and blue"),
    ])

    example_material_material: bpy.props.PointerProperty(name="Material", type=bpy.types.Material)

    example_driver_add: bpy.props.FloatProperty(name="Add", default=0.0)
    example_driver_factor: bpy.props.FloatProperty(name="Factor", default=1.0)
    example_driver_additive: bpy.props.EnumProperty(name="Additive", items=[
        ("off", "Off", ""),
        ("rotation", "For rotation only", ""),
        ("all", "All", ""),
    ], description="Use additive=True in the driver expression")
    example_randomize_location: bpy.props.BoolProperty(name="Randomize Location", default=False)
    example_randomize_rotation: bpy.props.FloatProperty(name="Randomize Rotation", default=0, min=0, max=1)
    example_randomize_scale: bpy.props.FloatProperty(name="Randomize Scale", default=0, min=0, max=1)
    example_rangeperobject: bpy.props.IntProperty(name="Frequency Range per Object (Hz)", default=100, min=1, max=1000,
                                                  description="Each object will react to this range of frequencies")
    example_freq_step_enable: bpy.props.BoolProperty(name="Set Custom Step", default=False)
    example_freq_step: bpy.props.FloatProperty(name="Frequency Step ", default=5.0, soft_min=0, soft_max=1000,
                                               description="If set to 5, objects will use"
                                                           " frequencies 0-50, 5-55, 10-60...")
    example_freqstart: bpy.props.FloatProperty(name="Frequency Start", default=0, min=0)
    example_objectsize_type: bpy.props.EnumProperty(name="Object Size Calculation", items=[
        ("relative", "Relative", "Calculated from X/Y/Z Count and from Collection Size"),
        ("fixed", "Fixed", ""),
        ("keep", "Keep", ""),
    ])
    example_objectsize_fixed_value: bpy.props.FloatVectorProperty(name="Fixed Object Size", default=(.1, .1, .1),
                                                                  subtype='TRANSLATION')
    example_objectsize: bpy.props.FloatProperty(name="Single Object Size Factor", default=1)
    example_width: bpy.props.FloatProperty(name="Collection Size", default=5, min=.01,
                                           description="Objects will be distributed in this range")
    example_object_type: bpy.props.EnumProperty(name="Objects Type", default="Cube", items=[
        ("Cube", "Cube", "Cube"),
        ("Suzanne", "Suzanne", "Suzanne"),
        ("Select Object:", "Select Object:", "Select Object:"),
        ("Random From Collection:", "Random From Collection:", "Random From Collection:"),
    ])
    example_object: bpy.props.PointerProperty(name="Object to Copy", type=bpy.types.Object)
    example_collection: bpy.props.PointerProperty(name="Collection to Choose Object", type=bpy.types.Collection,
                                                  poll=generator.collection_poll)
    example_lattice: bpy.props.BoolProperty(name="Lattice Object and Modifiers", default=True)
    example_empty: bpy.props.BoolProperty(name="Empty Parent", default=True,
                                          description="Create a parent of type Empty for all created objects."
                                                      " You can affect all created objects by"
                                                      " moving/resizing/rotating this empty object")

    example_shape: bpy.props.EnumProperty(name="Shape", default="grid", items=[
        ("grid", "Grid", "Objects will be placed in a grid"),
        ("circle", "Circle", "Objects will be placed around a circle"),
        ("curve", "Curve", "Objects will be placed along the selected Curve object"),
        ("point", "Single Point", "All objects will be at the same place")
    ])
    example_circle_radius: bpy.props.FloatProperty(name="Inner Radius", default=4,
                                                   description="Inner circle radius")
    example_curve_object: bpy.props.PointerProperty(name="Curve Object", type=bpy.types.Object,
                                                    poll=generator.curve_poll)
    example_curve_axis: bpy.props.EnumProperty(name="Curve Axis", default="FORWARD_X", items=[
        ("FORWARD_X", "X", ""),
        ("FORWARD_Y", "Y", ""),
        ("FORWARD_Z", "Z", ""),
        ("TRACK_NEGATIVE_X", "-X", ""),
        ("TRACK_NEGATIVE_Y", "-Y", ""),
        ("TRACK_NEGATIVE_Z", "-Z", ""),
    ])
    example_collections_action: bpy.props.EnumProperty(name="Collections", default="remove+new", items=[
        ("remove+new", "Replace by New Ones", ""),
        ("keep+new", "Keep and Create New Ones", ""),
        ("reuse", "Reuse", ""),
    ])
    example_sound_sequence: bpy.props.StringProperty(name="Sequence", default="")
    example_sequence_channel: bpy.props.IntProperty(name="Sequence Channel", default=0, min=0,
                                                    description="Channel number in Video Sequence Editor")
