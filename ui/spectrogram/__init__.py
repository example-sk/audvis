import bpy
from bpy.types import (
    Panel,
    Operator,
    UIList,
)

from . import bake
from .. import ui_lib
from ..buttonspanel import SequencerButtonsPanel, SequencerButtonsPanel_Npanel
from ..hz_label import hz_label, notes_label

from .operators import (
    spectrogramAdd,
    spectrogramDuplicate,
    spectrogramRemove,
    spectrogramSingleToMulti,
)

import string
import random


def calc_freq_step(self):
    if self.freq_step_enable:
        return self.freq_step
    return self.freqrange


class AUDVIS_UL_spectrogramList(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'IMAGE'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "enable", text="")
            layout.label(text=item.image.name)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)


class AUDVIS_PT_spectrogram(Panel):
    bl_label = "Spectrogram"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        col = self.layout.column(align=True)
        if context.scene.audvis.spectrogram_meta.mode == 'single':
            col.prop(context.scene.audvis.spectrogram, "enable", text="")
        else:
            col.prop(context.scene.audvis.spectrogram_meta, "enable", text="")

    def draw(self, context):
        col = self.layout.column(align=True)
        col.label(text="Spectrogram generator")
        col.prop(context.scene.audvis.spectrogram_meta, "mode", text="Mode")
        if context.scene.audvis.spectrogram_meta.mode == 'single':
            spect_props = context.scene.audvis.spectrogram
            col.operator('audvis.spectrogram_single_to_multi')
            self._draw_spectrogram(context, spect_props)
        else:
            col.template_list("AUDVIS_UL_spectrogramList", "spectrogram_list",
                              context.scene.audvis, "spectrograms",
                              context.scene.audvis.spectrogram_meta, "index")
            row = col.row()
            row.operator("audvis.spectrogram_add", text="Add")
            row.operator("audvis.spectrogram_duplicate", text="Duplicate")
            row.operator("audvis.spectrogram_remove", text="Remove")
            if context.scene.audvis.spectrogram_meta.index < len(context.scene.audvis.spectrograms):
                col = self.layout.column(align=True)
                selected_spectrogram = context.scene.audvis.spectrograms[context.scene.audvis.spectrogram_meta.index]
                # col.prop(selected_spectrogram, 'name')
                col.prop(selected_spectrogram.image, 'name', text="Image Name", icon="IMAGE")
                col.prop(selected_spectrogram.image, 'file_format', text="Format")
                col.prop(selected_spectrogram.image, 'use_half_precision')
                self._draw_spectrogram(context, selected_spectrogram)

    def _draw_spectrogram(self, context, spect_props):
        col = self.layout.column(align=True)
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
            whole_range_text = notes_label(count, spect_props.note_step, spect_props.note_a4_freq,
                                           spect_props.note_offset)
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

        col.prop(spect_props, "factor_float")
        col.prop(spect_props, "factor")
        col = self.layout.column(align=True)
        col.prop(spect_props, "skip_frames")

        col = self.layout.column(align=True)
        col.prop(spect_props, "operation")
        col.prop(spect_props, "clear_on_first_frame")
        col.prop(spect_props, "color")

        if spect_props.enable:
            col = self.layout.column(align=True)
            col.separator()
            col.operator('audvis.spectrogram_bake')


class AUDVIS_PT_spectrogramScene(AUDVIS_PT_spectrogram, SequencerButtonsPanel):
    bl_parent_id = "AUDVIS_PT_audvisScene"


class AUDVIS_PT_spectrogramNpanel(AUDVIS_PT_spectrogram, SequencerButtonsPanel_Npanel):
    pass


classes = bake.classes + [
    AUDVIS_PT_spectrogramScene,
    AUDVIS_PT_spectrogramNpanel,
    AUDVIS_UL_spectrogramList,
    spectrogramRemove.AUDVIS_OT_spectrogramRemove,
    spectrogramAdd.AUDVIS_OT_spectrogramAdd,
    spectrogramDuplicate.AUDVIS_OT_spectrogramDuplicate,
    spectrogramSingleToMulti.AUDVIS_OT_spectrogramSingleToMulti,
]
