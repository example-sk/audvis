import bpy
from bpy.types import (Operator, UIList)

from .buttonspanel import AudVisButtonsPanel_Npanel


def _seq_has_error(name):
    if bpy.audvis.sequence_analyzers is None:
        return False
    analyzer = bpy.audvis.sequence_analyzers.get(name, None)
    if analyzer is None:
        return False
    return analyzer.load_error is not None


def _get_selected_sound_sequence(context):
    if context.scene.sequence_editor is None:
        return None
    props = context.scene.audvis
    if 0 <= props.sequence_list_index < len(context.scene.sequence_editor.sequences_all):
        seq = context.scene.sequence_editor.sequences_all[props.sequence_list_index]
        if seq.type == 'SOUND':
            return seq
    return None


class AUDVIS_UL_soundSequenceList(UIList):
    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        ordered = [index for index, item in enumerate(items)]
        for i in range(len(items)):
            if items[i].type != 'SOUND':
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'SEQ_SEQUENCER'
        if _seq_has_error(item.sound.name):
            layout.alert = True
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item.audvis, "enable", text="")
            layout.label(text=item.name)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)


# copied from space_sequencer.py
def get_all_sound_sequences(context):
    try:
        ret = []
        for seq in context.scene.sequence_editor.sequences_all:
            if seq.type == 'SOUND':
                ret.append(seq)
        return ret
    except AttributeError:
        return []


class AUDVIS_OT_FrameAlign(Operator):
    bl_idname = "audvis.framealign"
    bl_label = "Align End Frame by Sequences"

    def execute(self, context):
        value = 1
        for seq in get_all_sound_sequences(context):
            value = max(value, seq.frame_final_end)
        context.scene.frame_end = value
        return {"FINISHED"}


class AUDVIS_OT_SequenceRemove(Operator):
    bl_idname = "audvis.sequence_remove"
    bl_label = "Remove Sound Sequence"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        if _get_selected_sound_sequence(context) is None:
            return False
        return True

    def execute(self, context):
        seq = _get_selected_sound_sequence(context)
        if seq is not None:
            for seq2 in list(context.scene.sequence_editor.sequences_all):
                seq2.select = False
            seq.select = True
            bpy.ops.sequencer.delete()
        return {'FINISHED'}


class AUDVIS_OT_SequenceAdd(Operator):
    bl_idname = "audvis.sequence_add"
    bl_label = "Add Sound Sequence"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        curr_area_type = context.area.type
        context.area.type = 'SEQUENCE_EDITOR'
        try:
            bpy.ops.sequencer.sound_strip_add('INVOKE_DEFAULT')
        except:
            pass
        finally:
            context.area.type = curr_area_type
        return {"FINISHED"}


class AUDVIS_PT_sequenceNpanel(AudVisButtonsPanel_Npanel):
    bl_label = "Sequence Analyzer"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.audvis, "sequence_enable", text="")

    def draw(self, context):
        props = context.scene.audvis
        layout = self.layout
        col = layout.column(align=True)
        col.template_list("AUDVIS_UL_soundSequenceList", "sound_sequence_list",
                          context.scene.sequence_editor, "sequences_all",
                          props, "sequence_list_index")
        row = col.row()
        row.operator("audvis.sequence_add")
        row.operator("audvis.sequence_remove")
        seq = _get_selected_sound_sequence(context)
        if seq is not None:
            col = layout.column(align=True)
            if _seq_has_error(seq.sound.name):
                col.alert = True
                col.label(text="File not found", icon="ERROR")
            col.prop(seq, "name")
            col.prop(seq, "frame_start")
            col.prop(seq, "frame_offset_start")
            col.prop(seq, "frame_final_duration")
        col = layout.column(align=True)
        col.prop(context.scene.audvis, "sequence_chunks")
        col.operator("audvis.framealign")


classes = [
    AUDVIS_OT_FrameAlign,
    AUDVIS_OT_SequenceRemove,
    AUDVIS_OT_SequenceAdd,
    AUDVIS_PT_sequenceNpanel,
    AUDVIS_UL_soundSequenceList,
]
