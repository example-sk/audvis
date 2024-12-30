import uuid
import bpy

from . import recording
from ..buttonspanel import AudVisButtonsPanel_Npanel


def input_device_options(self, context):
    audvis = bpy.audvis
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
        audvis = bpy.audvis
        audvis.input_device_options = None
        input_device_options(None, None)
        if audvis.realtime_analyzer:
            audvis.realtime_analyzer.restart()
        return {'FINISHED'}


class AUDVIS_PT_realtimeNpanel(AudVisButtonsPanel_Npanel):
    bl_label = "Real Time Analyzer"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        self.layout.prop(context.scene.audvis, "realtime_enable", text="")

    def draw(self, context):
        col = self.layout.column(align=True)
        # col.enabled = context.scene.audvis.realtime_enable
        supported = bpy.audvis.is_realtime_supported()
        if context.preferences.addons[bpy.audvis._module_name].preferences.realtime_device_use_global:
            col.label(text="Realtime device was set")
            col.label(text="in AudVis preferences")
        elif supported:
            col.prop(context.scene.audvis, 'realtime_multi_enable')
            if context.scene.audvis.realtime_multi_enable:
                self.draw_multi_mode(context, col)
            else:
                col.prop(context.scene.audvis, 'realtime_device')
                col.operator("audvis.realtime_reloaddevices")
        else:
            col.label(text="Realtime not supported. Install sounddevice first:")
            col.operator("audvis.install", text="Install python packages")
        err = bpy.audvis.get_realtime_error()
        col = self.layout.column(align=True)
        col.prop(context.scene.audvis, 'realtime_switchscenes')
        if err:
            col.label(text="Error: " + err)

    def draw_multi_mode(self, context, col):
        props = context.scene.audvis
        row = col.row()
        row.template_list("AUDVIS_UL_realtimeDeviceList", "realtime_multi_list", props,
                          "realtime_multi_list", props, "realtime_multi_index")
        row = col.row()
        row.operator('audvis.realtime_multi_add')
        row.operator('audvis.realtime_multi_remove')
        if len(props.realtime_multi_list) > 0:
            item_props = props.realtime_multi_list[props.realtime_multi_index]
            col = self.layout.column(align=True)
            col.label(text="Device name: {}".format(item_props.device_name))


class AUDVIS_OT_realtimeMultiAdd(bpy.types.Operator):
    bl_idname = "audvis.realtime_multi_add"
    bl_label = "Add RealTime Device Input"
    bl_description = ""
    bl_options = {'UNDO'}

    device: bpy.props.EnumProperty(name="Input Device", items=input_device_options)

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        res = context.window_manager.invoke_props_dialog(self, width=250)
        return res

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "device")
        # layout.popover('CYCLES_RENDER_PT_sampling')

    def execute(self, context):
        new_item = context.scene.audvis.realtime_multi_list.add()
        context.scene.audvis.realtime_multi_index = len(context.scene.audvis.realtime_multi_list) - 1
        new_item.uuid = uuid.uuid4().hex
        props = context.scene.audvis.realtime_multi_list[context.scene.audvis.realtime_multi_index]
        props.device_name = self.device
        try_name = self.device
        for i in range(2, 100):
            if try_name not in context.scene.audvis.realtime_multi_list:
                props.name = try_name
                break
            try_name = "{} {}".format(self.device, i)
        return {'FINISHED'}


class AUDVIS_OT_realtimeMultiRemove(bpy.types.Operator):
    bl_idname = "audvis.realtime_multi_remove"
    bl_label = "Remove RealTime Device Input"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        props = context.scene.audvis
        props.realtime_multi_list.remove(props.realtime_multi_index)
        if props.realtime_multi_index >= len(props.realtime_multi_list):
            props.realtime_multi_index = 0
        return {'FINISHED'}


class AUDVIS_UL_realtimeDeviceList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'OBJECT_DATAMODE'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "enable", text="")
            layout.prop(item, "name", text="", emboss=False)
            # layout.prop(item, "device_name", text="", emboss=False)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)


def unregister():
    try:
        bpy.audvis.realtime_analyzer.kill()
        bpy.audvis.realtime_analyzer = None
    except:
        pass
    try:
        for a in bpy.audvis.realtime_multi_analyzers.values():
            a.kill()
    except:
        pass
    bpy.audvis.realtime_multi_analyzers = {}


classes = [
              AUDVIS_OT_realtimeMultiAdd,
              AUDVIS_OT_realtimeMultiRemove,
              AUDVIS_UL_realtimeDeviceList,
              AUDVIS_PT_realtimeNpanel,
              AUDVIS_OT_RealtimeReloadDevices,
          ] + recording.classes
