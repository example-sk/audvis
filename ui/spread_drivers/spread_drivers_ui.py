from bpy.types import Panel

from .expression_builder import build_expression
from .. import ui_lib
from ..buttonspanel import SequencerButtonsPanel, SequencerButtonsPanel_Npanel


class AUDVIS_PT_spreaddrivers(Panel):
    bl_label = "Spread the Drivers"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        scene = context.scene
        props = scene.audvis.spreaddrivers
        col = self.layout.column(align=True)
        col.prop(props, "freq_seq_type")
        if props.freq_seq_type == "classic":
            col.prop(props, "freqrange")
            col.prop(props, "freqstart")
            col.prop(props, "freq_step_enable")
            if props.freq_step_enable:
                col.prop(props, "freq_step")
        elif props.freq_seq_type == "notes":
            col.prop(props, "note_a4_freq")
            col.prop(props, "note_step")
            col.prop(props, "note_offset")
        elif props.freq_seq_type == "midi":
            col.prop(props.midi, "offset")

        col.prop(props, "factor")
        col.prop(props, "add")
        if props.freq_seq_type != "midi":
            col.prop(props, "additive")
        col.prop(props, "freq_seq_type")
        if props.freq_seq_type == "midi":
            ui_lib.generators_ui_midi(self, context, props.midi)
        else:
            ui_lib.generators_ui_sequence(self, context, props)
        col = self.layout.column(align=True)
        col.prop(props, "expression")
        col.prop(props, "iteration")
        col.label(text="Next expression:")
        col.label(text=build_expression(props))


class AUDVIS_PT_spreaddriversScene(AUDVIS_PT_spreaddrivers, SequencerButtonsPanel):
    bl_parent_id = "AUDVIS_PT_audvisScene"


class AUDVIS_PT_spreaddriversNpanel(AUDVIS_PT_spreaddrivers, SequencerButtonsPanel_Npanel):
    pass


classes = [
    AUDVIS_PT_spreaddriversScene,
    AUDVIS_PT_spreaddriversNpanel,
]
