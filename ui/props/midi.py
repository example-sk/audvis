import bpy

from .. import midi as ui_midi


# midi_port = global_settings.GlobalSettings('midi_device')
# midi_enable = global_settings.GlobalSettings('midi_enable', default=False)


class AudvisMidiInputProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable", default=True)
    input_name: bpy.props.EnumProperty(name="Input Device", items=ui_midi.input_device_options)


class AudvisMidiProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable Midi Realtime", default=False)
    list_index: bpy.props.IntProperty(name="List Index", default=1)
    inputs: bpy.props.CollectionProperty(name="Midi Inputs", type=AudvisMidiInputProperties)


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
        for fcurve in scene.animation_data.action.fcurves:
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
    AudvisMidiProperties,
]
