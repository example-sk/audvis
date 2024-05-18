import bpy
from glob import glob
import os
import subprocess
import sys
from bpy.types import (UIList, Operator)

from ...utils import midi_number_to_note
from .. import install_lib
from ..buttonspanel import (AudVisButtonsPanel_Npanel)
from ...analyzer.midi_realtime import _MidiNoteMessage
from ...analyzer.midi_realtime.midi_thread import _MidiControlMessage


def input_device_options_with_none(self, context):
    return [('none', 'None', '')] + input_device_options(self, context)


def input_device_options(self, context):
    audvis = sys.modules['audvis'].audvis
    if audvis.midi_input_device_options is None:
        libs_path = install_lib.get_libs_path_latest()
        add_params = []
        if libs_path is not None:
            add_params = [
                '--libs-path',
                libs_path,
            ]
        f = glob(os.path.join(os.path.realpath(sys.prefix), 'bin', 'python*'))
        python_path = f[0]
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                   'analyzer/midi_realtime/midi_realtime_inputlist_proxy.py')
        print(" ".join([python_path,
                        script_path,
                        ] + add_params))
        process = subprocess.Popen([python_path,
                                    script_path,
                                    ] + add_params,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True
                                   )
        delimiter = False
        ret = []
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line == '---- delimiter ----':
                delimiter = True
            elif delimiter:
                ret.append((line, line, line))
        audvis.midi_input_device_options = ret
    return audvis.midi_input_device_options


class AUDVIS_OT_midiRealtimeDebug(Operator):
    bl_idname = "audvis.midi_realtime_debug"
    bl_label = "Debug Realtime Midi Messages"
    bl_description = ""
    timer = None

    @classmethod
    def poll(cls, context):
        return context.scene.audvis.midi_realtime.enable

    def execute(self, context):
        print("EXECUTE")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.workspace.status_text_set('MIDI REALTIME DEBUG started')
        self.timer = context.window_manager.event_timer_add(.2, window=context.window)
        context.window_manager.modal_handler_add(self)
        analyzer = sys.modules['audvis'].audvis.get_midi_realtime_analyzer(context.scene)
        if analyzer is not None:
            analyzer.on_pre_frame(context.scene, context.scene.frame_current_final)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            analyzer = sys.modules['audvis'].audvis.get_midi_realtime_analyzer(context.scene)
            if analyzer is not None:
                analyzer.on_pre_frame(context.scene, context.scene.frame_current_final)
                msg = analyzer.get_last_msg()
                if type(msg) == _MidiNoteMessage:
                    context.workspace.status_text_set(
                        "MIDI note: {} ({})"
                        " velocity: {}"
                        " channel: {}"
                        " device: {}".format(
                            msg.note,
                            midi_number_to_note(msg.note),
                            msg.velocity,
                            msg.channel,
                            msg.input_name
                        ))
                elif type(msg) == _MidiControlMessage:
                    context.workspace.status_text_set(
                        "MIDI control: {}"
                        " value: {}"
                        " channel: {}"
                        " device: {}".format(
                            msg.control,
                            msg.value,
                            msg.channel,
                            msg.input_name
                        ))
            return {'PASS_THROUGH'}
        elif event.type == 'ESC':
            context.workspace.status_text_set("")
            context.window_manager.event_timer_remove(self.timer)
            return {'FINISHED'}
        return {'PASS_THROUGH'}


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


class AUDVIS_PT_midiRealtimeNpanel(AudVisButtonsPanel_Npanel):
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
        col.operator("audvis.midi_realtime_debug", icon="INFO")


classes = [
    AUDVIS_PT_midiRealtimeNpanel,
    AUDVIS_UL_midiInputList,
    AUDVIS_OT_midiInputAdd,
    AUDVIS_OT_midiInputRemove,
    AUDVIS_OT_midiRealtimeRestart,
    AUDVIS_OT_midiRealtimeDebug,
]
