import sys

import bpy
from bpy.types import Panel

from . import recording
from ..buttonspanel import SequencerButtonsPanel, SequencerButtonsPanel_Npanel


def input_device_options(self, context):
    audvis = sys.modules['audvis'].audvis
    if audvis.input_device_options is None:
        import sounddevice as sd
        ret = [
            ('_auto_', '- Auto -', "Default")
        ]
        devices = sd.query_devices()
        for i in range(len(devices)):
            d = devices[i]
            if d['max_input_channels'] > 0:
                # (identifier, name, description)
                ret.append((d['name'], d['name'], d['name']))
        audvis.input_device_options = ret
    return audvis.input_device_options


class AUDVIS_OT_RealtimeReloadDevices(bpy.types.Operator):
    bl_idname = "audvis.realtime_reloaddevices"
    bl_label = "Reconnect and reload device list"

    def execute(self, context):
        audvis = sys.modules['audvis'].audvis
        audvis.input_device_options = None
        input_device_options(None, None)
        if audvis.realtime_analyzer:
            audvis.realtime_analyzer.restart()
        return {'FINISHED'}


class AUDVIS_PT_realtime(Panel):
    bl_label = "Real Time Analyzer"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        self.layout.prop(context.scene.audvis, "realtime_enable", text="")

    def draw(self, context):
        col = self.layout.column(align=True)
        # col.enabled = context.scene.audvis.realtime_enable
        supported = sys.modules['audvis'].audvis.is_realtime_supported()
        if supported:
            col.prop(context.scene.audvis, 'realtime_device')
            col.operator("audvis.realtime_reloaddevices")

        else:
            col.label(text="Realtime not supported. Install sounddevice first:")
            col.operator("audvis.install", text="Install python packages")
        err = sys.modules['audvis'].audvis.get_realtime_error()
        col.prop(context.scene.audvis, 'realtime_switchscenes')
        if err:
            col.label(text="Error: " + err)


class AUDVIS_PT_realtimeScene(AUDVIS_PT_realtime, SequencerButtonsPanel):
    bl_parent_id = "AUDVIS_PT_audvisScene"


class AUDVIS_PT_realtimeNpanel(AUDVIS_PT_realtime, SequencerButtonsPanel_Npanel):
    pass


def unregister():
    try:
        sys.modules['audvis'].audvis.realtime_analyzer.kill()
        sys.modules['audvis'].audvis.realtime_analyzer = None
    except:
        pass


classes = [
              AUDVIS_PT_realtimeScene,
              AUDVIS_PT_realtimeNpanel,
              AUDVIS_OT_RealtimeReloadDevices,
          ] + recording.classes
