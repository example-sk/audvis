import bpy
from bpy.types import (
    Panel,
)

from . import bake
from .. import ui_lib
from ..buttonspanel import SequencerButtonsPanel, SequencerButtonsPanel_Npanel
from ..hz_label import hz_label, notes_label


def calc_freq_step(self):
    if self.freq_step_enable:
        return self.freq_step
    return self.freqrange


class AUDVIS_PT_spectrogram(Panel):
    bl_label = "Spectrogram"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.audvis.spectrogram, "enable", text="")

    def draw(self, context):
        col = self.layout.column(align=True)
        col.label(text="Spectrogram generator")
        col.label(text="Warning: this can be pretty CPU intensive")
        spect_props = context.scene.audvis.spectrogram
        col.prop(spect_props, "freq_seq_type")
        if spect_props.freq_seq_type == "classic":
            col.prop(spect_props, "freqrange")
            col.prop(spect_props, "freqstart")
            col.prop(spect_props, "freq_step_enable")
            if spect_props.freq_step_enable:
                col.prop(spect_props, "freq_step")
        elif spect_props.freq_seq_type == "notes":
            col.prop(spect_props, "note_a4_freq")
            col.prop(spect_props, "note_step")
            col.prop(spect_props, "note_offset")
        elif spect_props.freq_seq_type == "midi":
            col.prop(spect_props.midi, "offset")


        col = self.layout.column(align=True)
        col.prop(spect_props, "mode")
        col.prop(spect_props, "width")
        rows = 1
        if spect_props.mode != 'one-big':
            col.prop(spect_props, "height")
        if spect_props.mode == 'snapshot':
            rows = spect_props.height

        count = spect_props.width
        if spect_props.mode == 'snapshot':
            count *= spect_props.height
        if spect_props.freq_seq_type == 'midi':
            whole_range_text = None
        elif spect_props.freq_seq_type == 'notes':
            whole_range_text = notes_label(count, spect_props.note_step, spect_props.note_a4_freq, spect_props.note_offset)
        else:
            whole_range_text = hz_label(start=spect_props.freqstart,
                                        range_per_point=spect_props.freqrange,
                                        step=calc_freq_step(spect_props),
                                        points_count=count)
        if whole_range_text is not None:
            col.label(text=whole_range_text)
        if spect_props.freq_seq_type == 'midi':
            ui_lib.generators_ui_midi(self, context, spect_props.midi)
        else:
            ui_lib.generators_ui_sequence(self, context, spect_props)

        col.prop(spect_props, "factor")
        col = self.layout.column(align=True)
        col.prop(spect_props, "skip_frames")

        col = self.layout.column(align=True)
        col.prop(spect_props, "operation")
        col.prop(spect_props, "clear_on_first_frame")
        col.prop(spect_props, "color")

        if spect_props.enable:
            col = self.layout.column(align=True)
            col.prop(spect_props, "bake_path")
            col.operator('audvis.spectrogram_bake')
            if not bpy.data.is_saved:
                col.alert=True
                col.label(text=".blend file must be saved")
                col.label(text="before baking the Spectrogram")
            else:
                col.label(text="After baking, you have to")
                col.label(text="load the image sequence manually")
                col.label(text="where needed.")


class AUDVIS_PT_spectrogramScene(AUDVIS_PT_spectrogram, SequencerButtonsPanel):
    bl_parent_id = "AUDVIS_PT_audvisScene"


class AUDVIS_PT_spectrogramNpanel(AUDVIS_PT_spectrogram, SequencerButtonsPanel_Npanel):
    pass


classes = bake.classes + [
    AUDVIS_PT_spectrogramScene,
    AUDVIS_PT_spectrogramNpanel,
]
