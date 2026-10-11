import bpy

from ...utils import action_get_fcurves
from .. import midi as ui_midi


# midi_port = global_settings.GlobalSettings('midi_device')
# midi_enable = global_settings.GlobalSettings('midi_enable', default=False)


class AudvisMidiInputProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable", default=True)
    input_name: bpy.props.EnumProperty(name="Input Device", items=ui_midi.input_device_options)


def _map_update(self, context):
    ui_midi.mapping.forget(self)


class AudvisMidiMapProperties(bpy.types.PropertyGroup):
    """A knob / fader / pad of a MIDI controller mapped to a property or an action."""
    enable: bpy.props.BoolProperty(name="Enable", default=True)
    uid: bpy.props.StringProperty()
    # source
    kind: bpy.props.EnumProperty(name="Type", items=[
        ('cc', "CC", "Knob, fader or CC button"),
        ('note', "Note", "Pad or key"),
    ], update=_map_update)
    number: bpy.props.IntProperty(name="Number", min=0, max=127, update=_map_update,
                                  description="CC number or note number")
    channel: bpy.props.IntProperty(name="Channel", default=0, min=0, max=16, update=_map_update,
                                   description="MIDI channel, 0 = any")
    device: bpy.props.StringProperty(name="Device", update=_map_update,
                                     description="Only this input device. Empty = any")
    # target
    target: bpy.props.EnumProperty(name="Controls", items=[
        ('property', "Property", "A value in Blender (AudVis or native)"),
        ('action', "Action", "Press to do something"),
    ], update=_map_update)
    full_path: bpy.props.StringProperty(name="Data Path", update=ui_midi.mapping.on_path_update,
                                        description="Right-click a property > Copy Full Data Path, paste here."
                                                    " Or right-click it > AudVis: MIDI Learn")
    id_type: bpy.props.StringProperty()
    id_name: bpy.props.StringProperty()
    data_path: bpy.props.StringProperty()
    index: bpy.props.IntProperty(default=-1)
    action: bpy.props.EnumProperty(name="Action", items=[
        ('play', "Play / Pause", ""),
        ('next_scene', "Next Scene", "Like the Scenes grid, in project order"),
        ('prev_scene', "Previous Scene", ""),
        ('scene', "Go to Scene", ""),
        ('engage', "Motion FX: Engage All", ""),
        ('release', "Motion FX: Release All", ""),
        ('stop', "Motion FX: Stop All", ""),
    ], update=_map_update)
    scene_name: bpy.props.StringProperty(name="Scene")
    # response
    response: bpy.props.EnumProperty(name="Response", items=[
        ('range', "Fader / Knob", "Follow the knob (pads: velocity while held)"),
        ('momentary', "Hold", "Max while pressed, Min when released"),
        ('toggle', "Toggle", "Each press switches between Min and Max"),
    ], update=_map_update)
    range_min: bpy.props.FloatProperty(name="Min", default=0, update=_map_update)
    range_max: bpy.props.FloatProperty(name="Max", default=1, update=_map_update)
    invert: bpy.props.BoolProperty(name="Invert", default=False)
    curve: bpy.props.FloatProperty(name="Curve", default=1, min=.1, max=10,
                                   description="1 = linear. Higher = finer control at the low end")
    smoothing: bpy.props.FloatProperty(name="Smoothing", default=0, min=0, max=.98, subtype='FACTOR',
                                       description="Glide to the knob value instead of jumping")
    pickup: bpy.props.BoolProperty(name="Pickup", default=False, update=_map_update,
                                   description="Don't jump: wait until the knob reaches the current value."
                                               " For when the value was changed with the mouse or a scene switch")
    record: bpy.props.BoolProperty(name="Record", default=False,
                                   description="While playing, insert keyframes as you move the knob")


class AudvisMidiProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable Midi Realtime", default=False)
    list_index: bpy.props.IntProperty(name="List Index", default=1)
    inputs: bpy.props.CollectionProperty(name="Midi Inputs", type=AudvisMidiInputProperties)
    maps: bpy.props.CollectionProperty(name="MIDI Mappings", type=AudvisMidiMapProperties)
    maps_index: bpy.props.IntProperty(name="Active Mapping", default=0)


class AudvisMidiTrackProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable Midi Realtime", default=True)
    deleted: bpy.props.BoolProperty(name="Deleted", default=False)


class AudvisMidiFileProperties(bpy.types.PropertyGroup):  # custom properties for sequences are not animatable
    enable: bpy.props.BoolProperty(name="Enable", default=True)
    tracks: bpy.props.CollectionProperty(name="Midi Tracks", type=AudvisMidiTrackProperties)
    time_length: bpy.props.FloatProperty(name="Length in Seconds")
    fps_when_loaded: bpy.props.FloatProperty(name="FPS when loaded into .blend")
    list_index: bpy.props.IntProperty(name="List Index")
    filepath: bpy.props.StringProperty(name="Midi File Path")
    bpm: bpy.props.IntProperty(name="BPM")
    frame_start: bpy.props.IntProperty(name="Frame Start")
    animation_offset_start: bpy.props.IntProperty(name="Hold Offset Start", min=0)
    animation_offset_end: bpy.props.IntProperty(name="Hold Offset End", min=0)
    deleted: bpy.props.BoolProperty(name="Deleted", default=False)

    def fix_fps(self):
        scene = self.id_data
        old_fps = self.fps_when_loaded
        new_fps = scene.render.fps / scene.render.fps_base
        fps_ratio = new_fps / old_fps
        if new_fps == old_fps:
            return
        base_data_path = self.path_from_id()
        for fcurve in action_get_fcurves(scene.animation_data.action):
            if not fcurve.data_path.startswith(base_data_path):
                continue
            for point in fcurve.keyframe_points:
                point.co[0] *= fps_ratio
            fcurve.update()
        self.fps_when_loaded = new_fps


class AudvisMidiFilesProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable", default=False)
    list_index: bpy.props.IntProperty(name="List Index")
    midi_files: bpy.props.CollectionProperty(name="Midi File List", type=AudvisMidiFileProperties)


class AudvisMidiGeneratorsProperties(bpy.types.PropertyGroup):
    offset: bpy.props.IntProperty(name="MIDI Note Offset", default=0)
    file: bpy.props.StringProperty(name="MIDI FIle")
    track: bpy.props.StringProperty(name="MIDI Track", default='')
    channel: bpy.props.EnumProperty(name="MIDI Channel",
                                    default='all',
                                    items=[('all', 'All', '')] + [(str(i + 1), str(i + 1), "") for i in range(16)])
    device: bpy.props.StringProperty(name="MIDI Input Device")


classes = [
    AudvisMidiGeneratorsProperties,
    AudvisMidiTrackProperties,
    AudvisMidiFileProperties,
    AudvisMidiFilesProperties,
    AudvisMidiInputProperties,
    AudvisMidiMapProperties,
    AudvisMidiProperties,
]
