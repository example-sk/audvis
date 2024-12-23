import bpy
from .. import realtime


class AudvisRealtimeProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Realtime Source Enable", default=True)
    device: bpy.props.EnumProperty(name="Input Device", items=realtime.input_device_options)
    device_name: bpy.props.StringProperty(name="Device Name")
    uuid: bpy.props.StringProperty()


classes = [
    AudvisRealtimeProperties
]
