import bpy
from bpy.types import (
    Panel,
)

from . import generate
from .. import ui_lib
from ..buttonspanel import SequencerButtonsPanel, SequencerButtonsPanel_Npanel
from ..hz_label import hz_label, notes_label


def calc_freq_step(self):
    if self.freq_step_enable:
        return self.freq_step
    return self.freqrange


class AUDVIS_PT_ArmatureGenerator(Panel):
    bl_label = "Generate Armature"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        obj = context.active_object or context.object
        col = layout.column(align=True)
        if not (obj and obj.type == 'MESH'):
            col.label(text="Select a mesh object")
            return
        col.label(text="Selected faces will be used")
        props = obj.audvis.armature_generator
        col.prop(props, "inset")
        if props.inset:
            col.label(text="Warning: Don't use this")
            col.label(text="option repeatedly")
            col.prop(props, "inset_and_extrude")
            col.prop(props, "inset_size")
        col = layout.column(align=True)
        col.prop(props, "factor")
        col = layout.column(align=True)

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
        count = len([1 for p in obj.data.polygons if p.select])
        col.label(text="Toggle edit mode to update")
        col.label(text="the number of selected faces")
        if count:
            if props.freq_seq_type == 'midi':
                whole_range_text = None
            elif props.freq_seq_type == 'notes':
                whole_range_text = notes_label(count, props.note_step, props.note_a4_freq, props.note_offset)
            else:
                whole_range_text = hz_label(start=props.freqstart,
                                            range_per_point=props.freqrange,
                                            step=calc_freq_step(props),
                                            points_count=count)
            if whole_range_text is not None:
                col.label(text=whole_range_text)
            if props.freq_seq_type == 'midi':
                ui_lib.generators_ui_midi(self, context, props.midi)
            else:
                ui_lib.generators_ui_sequence(self, context, props)
            col = layout.column(align=False)
            col.prop(props, "keep_old_vgroups")
            col.operator("audvis.generate_armature")


class AUDVIS_PT_ArmatureGeneratorScene(AUDVIS_PT_ArmatureGenerator, SequencerButtonsPanel):
    bl_parent_id = "AUDVIS_PT_audvisScene"


class AUDVIS_PT_ArmatureGeneratorNpanel(AUDVIS_PT_ArmatureGenerator, SequencerButtonsPanel_Npanel):
    pass

class AUDVIS_OT_Generate(bpy.types.Operator):
    bl_idname = "audvis.generate_armature"
    bl_label = "Generate AudVis Armature"

    @classmethod
    def poll(cls, context):
        if context.active_object or context.object:
            return True
        return False

    def execute(self, context):
        generate.generate(context)
        return {'FINISHED'}


classes = [
    AUDVIS_PT_ArmatureGeneratorNpanel,
    AUDVIS_PT_ArmatureGeneratorScene,
    AUDVIS_OT_Generate,
]
