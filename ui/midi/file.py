import sys

from bpy.types import (Operator, Panel, UIList)
from .operators import (
    midiFileRemove,
    midiFileOpen,
    midiTrackRemove,
)

from ..buttonspanel import (SequencerButtonsPanel, SequencerButtonsPanel_Npanel)
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
    midiFileOpen.AUDVIS_OT_midiFileOpen,
    midiFileRemove.AUDVIS_OT_midiFileRemove,
    midiTrackRemove.AUDVIS_OT_midiTrackRemove,
]
