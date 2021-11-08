import sys

from bpy.types import (Panel, UIList, Operator)

from ..buttonspanel import (SequencerButtonsPanel, SequencerButtonsPanel_Npanel)


def input_device_options_with_none(self, context):
    return [('none', 'None', '')] + input_device_options(self, context)


def input_device_options(self, context):
    audvis = sys.modules['audvis'].audvis
    if audvis.midi_input_device_options is None:
        mido = sys.modules['audvis'].audvis.get_mido()
        ret = [
            # ('_auto_', '- Auto -', "Default")
        ]
        for name in mido.get_input_names():
            ret.append((name, name, name))
        audvis.midi_input_device_options = ret
    return audvis.midi_input_device_options


class AUDVIS_OT_midiRealtimeRestart(Operator):
    bl_idname = "audvis.midi_realtime_restart"
    bl_label = "Restart Midi Inputs"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        audvis = sys.modules['audvis'].audvis
        analyzer = audvis.get_midi_realtime_analyzer(context.scene)
        if analyzer is not None:
            analyzer.restart()
        return {'FINISHED'}


class AUDVIS_OT_midiInputAdd(Operator):
    bl_idname = "audvis.midi_input_add"
    bl_label = "Add Midi Input"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        audvis = sys.modules['audvis'].audvis
        audvis.midi_input_device_options = None
        props = context.scene.audvis.midi_realtime
        props.inputs.add()
        props.list_index = len(props.inputs) - 1
        i = len(props.inputs)
        name = 'MIDI Device {}'.format(i)
        for j in range(1000):
            if name in props.inputs:
                i += 1
                name = 'MIDI Device {}'.format(i)
            else:
                break
        props.inputs[-1].name = name
        return {'FINISHED'}


class AUDVIS_OT_midiInputRemove(Operator):
    bl_idname = "audvis.midi_input_remove"
    bl_label = "Remove Midi Input"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        props = context.scene.audvis.midi_realtime
        props.inputs.remove(props.list_index)
        return {'FINISHED'}


class AUDVIS_UL_midiInputList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'OBJECT_DATAMODE'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "enable", text="")
            layout.label(text=item.name, icon=custom_icon)
            layout.label(text=item.input_name)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)


class AUDVIS_PT_midiRealtime(Panel):
    bl_label = "Midi Realtime"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        self.layout.prop(context.scene.audvis.midi_realtime, "enable", text="")

    def draw(self, context):
        layout = self.layout
        props = context.scene.audvis.midi_realtime
        col = layout.column(align=True)
        supported = sys.modules['audvis'].audvis.is_midi_realtime_supported()
        if not supported:
            col.label(text="Midi realtime not supported. Install mido first:")
            col.operator("audvis.install", text="Install python packages")
            return
        col.prop(props, "inputs")
        row = col.row()
        row.template_list("AUDVIS_UL_midiInputList", "midi_input_list", props,
                          "inputs", props, "list_index")
        row = col.row()
        row.operator('audvis.midi_input_add')
        row.operator('audvis.midi_input_remove')

        if 0 <= props.list_index < len(props.inputs):
            col = layout.column(align=True)
            item = props.inputs[props.list_index]
            col.prop(item, "name")
            col.prop(item, "input_name")

        col = layout.column(align=True)
        col.operator("audvis.midi_realtime_restart")


class AUDVIS_PT_midiRealtimeScene(AUDVIS_PT_midiRealtime, SequencerButtonsPanel):
    bl_parent_id = "AUDVIS_PT_audvisScene"


class AUDVIS_PT_midiRealtimeNpanel(AUDVIS_PT_midiRealtime, SequencerButtonsPanel_Npanel):
    pass


classes = [
    AUDVIS_PT_midiRealtimeNpanel,
    AUDVIS_PT_midiRealtimeScene,
    AUDVIS_UL_midiInputList,
    AUDVIS_OT_midiInputAdd,
    AUDVIS_OT_midiInputRemove,
    AUDVIS_OT_midiRealtimeRestart,
]
