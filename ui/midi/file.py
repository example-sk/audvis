from bpy.types import (Operator, UIList)
from .operators import (
    midiFileRemove,
    midiFileOpen,
    midiTrackRemove,
)
import bpy
import re

from ..buttonspanel import (AudVisButtonsPanel_Npanel)
from .utils import (get_selected_midi_file, get_selected_midi_track)


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


regexp = re.compile('ch([0-9]+)_(n|c)([0-9]+)')


class AUDVIS_PT_midiFileNpanel(AudVisButtonsPanel_Npanel):
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
        supported = bpy.audvis.is_midi_realtime_supported()
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
        midifile = get_selected_midi_file(context)
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
        track = get_selected_midi_track(context)
        midifile = get_selected_midi_file(context)
        if track is None:
            return
        col.prop(track, "name")
        col.operator('audvis.midi_track_remove')
        # col = layout.column(align=True)
        for key in track.keys():
            regexp_result = regexp.match(key)
            if regexp_result:
                channel = regexp_result.group(1)
                type = regexp_result.group(2)
                note = regexp_result.group(3)
                col.label(text="Driver expression (example):")
                expr = "audvis({}={}, ch={}, track={}, file={})".format(
                    "midi" if type == 'n' else "midi_control",
                    int(note),
                    int(channel),
                    repr(track.name),
                    repr(midifile.name)
                )
                col.label(text=expr)
                op = col.operator("audvis.copy_string", text="Copy Driver Expression to Clipboard")
                op.value = expr
                break


classes = [
    AUDVIS_UL_midiFileList,
    AUDVIS_UL_midiTrackList,
    AUDVIS_PT_midiFileNpanel,
    midiFileOpen.AUDVIS_OT_midiFileOpen,
    midiFileRemove.AUDVIS_OT_midiFileRemove,
    midiTrackRemove.AUDVIS_OT_midiTrackRemove,
]
