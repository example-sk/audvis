import bpy


class AudvisDawArrangement(bpy.types.PropertyGroup):
    filepath: bpy.props.StringProperty(name="File Path", subtype="FILE_PATH", description="*.dawproject or *.als file")
    zoom: bpy.props.FloatProperty(name="Zoom X", default=.3)
    thickness_clip: bpy.props.FloatProperty(name="Clip Thickness", default=.1)
    thickness_note: bpy.props.FloatProperty(name="Note Thickness", default=.05)
    zero_length_note_threshold: bpy.props.FloatProperty(name="Zero Length Note Threshold", default=.001, min=.0, precision=3)
    zero_length_note_size: bpy.props.FloatProperty(name="Zero Length Note Duration", default=.0, min=.0)
    frame_start: bpy.props.IntProperty(name="Start Frame", default=1)
    line_height: bpy.props.FloatProperty(name="Line Height", default=.5, min=0)
    line_margin: bpy.props.FloatProperty(name="Line Margin", default=.1)
    center_tracks: bpy.props.BoolProperty(name="Center Tracks", default=False, description="If enabled, tracks will be centered on Y axis. Otherwise they go from zero")
    clip_padding: bpy.props.FloatProperty(name="Clip Padding", default=10, min=0.0, max=100, subtype="PERCENTAGE")
    track_name_position: bpy.props.EnumProperty(name="Track Name Z Position", default=2, items=[
        ("0", "Under Clips", ""),
        ("1", "Between Clip and Notes", ""),
        ("2", "Above Notes", ""),
    ])
    track_name_bevel_depth: bpy.props.FloatProperty(name="Track Name Bevel Depth", default=0.0)
    # animate_property: bpy.props.EnumProperty(name="Animate Property", items=[
    #    ("location-x", "Location X", ""),
    #    ("geonodes-progress", 'Geometry Nodes Input "Progress"', ""),
    # ], default="location-x")
    output: bpy.props.EnumProperty(name="Output Object(s)", items=[
        ("geonodes1", "Geometry Nodes 1", ""),
        # ("geonodes2", "Geometry Nodes - Curves", ""),
    ], default="geonodes1")
    replace_last_collection: bpy.props.BoolProperty(name="Replace Last Collection", default=True)
    last_collection: bpy.props.PointerProperty(name="Last Collection", type=bpy.types.Collection)
    audio_internal_samplerate: bpy.props.IntProperty(name="Audio Internal Samplerate", default=50, min=1, max=10000)
    audio_use_abs: bpy.props.BoolProperty(name="Audio: Use Absolute Values", default=True)
    audio_horizontal: bpy.props.BoolProperty(name="Horizontal SoundWave", default=True)
    audio_curve_samplerate: bpy.props.IntProperty(name="Audio Curve Points Samplerate", default=50, min=1, max=10000)
    audio_algorithm: bpy.props.EnumProperty(name="Audio Algorithm", items=[
        ("raw", "Raw", ""),
        ("log", "Logarithm", ""),
    ])
    audio_amplitude: bpy.props.FloatProperty(name="Audio Amplitude", default=.1, min=.001, max=100)


classes = [
    AudvisDawArrangement
]
