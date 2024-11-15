import bpy

from .. import midi as ui_midi


# midi_port = global_settings.GlobalSettings('midi_device')
# midi_enable = global_settings.GlobalSettings('midi_enable', default=False)


class AudvisDawArrangement(bpy.types.PropertyGroup):
    filepath: bpy.props.StringProperty(name="File Path", subtype="FILE_PATH", description="*.dawproject or *.als file")
    input_name: bpy.props.EnumProperty(name="Input Device", items=ui_midi.input_device_options)
    zoom: bpy.props.FloatProperty(name="Zoom X", default=.3)
    thickness_clip: bpy.props.FloatProperty(name="Clip Thickness", default=.1)
    thickness_note: bpy.props.FloatProperty(name="Note Thickness", default=.05)
    frame_start: bpy.props.IntProperty(name="Start Frame", default=1)
    line_height: bpy.props.FloatProperty(name="Line Height", default=.5, min=0)
    line_margin: bpy.props.FloatProperty(name="Line Margin", default=.1)
    clip_padding: bpy.props.FloatProperty(name="Clip Padding", default=10, min=0.0, max=100, subtype="PERCENTAGE")
    track_name_position: bpy.props.EnumProperty(name="Track Name Z Position", items=[
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
    replace_last_collection: bpy.props.BoolProperty(name="Replace Last Collection")
    last_collection: bpy.props.PointerProperty(name="Last Collection", type=bpy.types.Collection)


classes = [
    AudvisDawArrangement
]