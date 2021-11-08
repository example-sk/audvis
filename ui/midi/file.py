import sys

import bpy
from bpy.types import (Operator, Panel, UIList)
from bpy_extras.io_utils import ImportHelper

from . import midi_file_baker
from ..buttonspanel import (SequencerButtonsPanel, SequencerButtonsPanel_Npanel)


def _get_selected_midi_file(context):
    props = context.scene.audvis.midi_file
    if 0 <= props.list_index < len(props.midi_files):
        midifile = props.midi_files[props.list_index]
        if midifile.deleted:
            return None
        return midifile
    return None


def _get_selected_midi_track(context):
    props = context.scene.audvis.midi_file
    midifile = _get_selected_midi_file(context)
    if midifile is None:
        return None
    if 0 <= midifile.list_index < len(midifile.tracks):
        track = midifile.tracks[midifile.list_index]
        if track.deleted:
            return None
        return track
    return None


class AUDVIS_OT_midiFileOpen(Operator, ImportHelper):
    bl_idname = "audvis.midi_file_open"
    bl_label = "Add Midi File"
    bl_description = ""

    filter_glob: bpy.props.StringProperty(
        default='*.mid',
        options={'HIDDEN'}
    )

    strip_silent_start: bpy.props.BoolProperty(
        name="Strip Silent Beginning of MIDI",
        description="MIDI files use to have sometimes quite a long time from beginning to first note."
                    " This cuts that empty, silent part.",
        default=True
    )

    @classmethod
    def poll(cls, context):
        return sys.modules['audvis'].audvis.is_midi_realtime_supported()

    def execute(self, context):
        midi_file_baker.bake(context.scene, self.filepath, self.strip_silent_start)

        return {'FINISHED'}


class AUDVIS_OT_midiFileRemove(Operator):
    bl_idname = "audvis.midi_file_remove"
    bl_label = "Remove Midi File"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        if not sys.modules['audvis'].audvis.is_midi_realtime_supported():
            return False
        if _get_selected_midi_file(context) is None:
            return False
        return True

    def execute(self, context):
        midifile = _get_selected_midi_file(context)
        if midifile is not None \
                and context.scene.animation_data \
                and context.scene.animation_data.action is not None:
            fcurves = context.scene.animation_data.action.fcurves
            for fcurve in fcurves:
                if fcurve.data_path.startswith(midifile.path_from_id()):
                    fcurves.remove(fcurve)
            midifile.deleted = True
            midifile.enable = False
            midifile.name = '_deleted'
            midifile.filepath = ''
            midifile.tracks.clear()
            # TODO: try to really delete? Check if fcurves work how expected
        return {'FINISHED'}


class AUDVIS_OT_midiTrackRemove(Operator):
    bl_idname = "audvis.midi_track_remove"
    bl_label = "Remove Midi Track"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        if not sys.modules['audvis'].audvis.is_midi_realtime_supported():
            return False
        if _get_selected_midi_track(context) is None:
            return False
        return True

    def execute(self, context):
        track = _get_selected_midi_track(context)
        if track is not None \
                and context.scene.animation_data \
                and context.scene.animation_data.action is not None:
            fcurves = context.scene.animation_data.action.fcurves
            for fcurve in fcurves:
                if fcurve.data_path.startswith(track.path_from_id()):
                    fcurves.remove(fcurve)
            track.deleted = True
            track.enable = False
            track.name = '_deleted'
            # TODO: try to really delete? Check if fcurves work how expected
        return {'FINISHED'}


class AUDVIS_UL_midiTrackList(UIList):
    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        ordered = [index for index, item in enumerate(items)]
        for i in range(len(items)):
            if items[i].deleted:
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "enable", text="")
            layout.label(text=item.name)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="")


class AUDVIS_UL_midiFileList(UIList):
    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        ordered = [index for index, item in enumerate(items)]
        for i in range(len(items)):
            if items[i].deleted:
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'SOUND'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "enable", text="")
            layout.label(text=item.name)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.name, icon=custom_icon)


class AUDVIS_PT_midiFile(Panel):
    bl_label = "Midi File"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        self.layout.prop(context.scene.audvis.midi_file, "enable", text="")

    def draw(self, context):
        layout = self.layout
        props = context.scene.audvis.midi_file
        col = layout.column(align=True)
        supported = sys.modules['audvis'].audvis.is_midi_realtime_supported()
        if not supported:
            col.label(text="Midi files not supported. Install mido first:")
            col.operator("audvis.install", text="Install python packages")
            return
        col.template_list("AUDVIS_UL_midiFileList", "midi_file_list",
                          context.scene.audvis.midi_file, "midi_files",
                          props, "list_index")
        row = col.row()
        row.operator('audvis.midi_file_open')
        row.operator('audvis.midi_file_remove')
        midifile = _get_selected_midi_file(context)
        if midifile is not None:
            col = layout.column(align=True)
            col.prop(midifile, "name")
            col.prop(midifile, "frame_start")
            col.prop(midifile, "animation_offset_start")
            col.prop(midifile, "animation_offset_end")
            col.label(text="Tracks for {}:".format(midifile.name))
            col.template_list("AUDVIS_UL_midiTrackList", "midi_track_list",
                              midifile, "tracks",
                              midifile, "list_index")
            self._draw_track_info(col, context)

    def _draw_track_info(self, col, context):
        track = _get_selected_midi_track(context)
        if track is None:
            return
        col.prop(track, "name")
        col.operator('audvis.midi_track_remove')


class AUDVIS_PT_midiFileScene(AUDVIS_PT_midiFile, SequencerButtonsPanel):
    bl_parent_id = "AUDVIS_PT_audvisScene"


class AUDVIS_PT_midiFileNpanel(AUDVIS_PT_midiFile, SequencerButtonsPanel_Npanel):
    pass


classes = [
    AUDVIS_UL_midiFileList,
    AUDVIS_UL_midiTrackList,
    AUDVIS_PT_midiFileNpanel,
    AUDVIS_PT_midiFileScene,
    AUDVIS_OT_midiFileOpen,
    AUDVIS_OT_midiFileRemove,
    AUDVIS_OT_midiTrackRemove,
]
