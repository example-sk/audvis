import bpy


class AudvisRealtimeItemProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Realtime Source Enable", default=True)
    device_name: bpy.props.StringProperty(name="Device Name")
    uuid: bpy.props.StringProperty()


class AudvisRealtimeMultiProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Multiple Sources Enable", default=False)
    list: bpy.props.CollectionProperty(type=AudvisRealtimeItemProperties)
    index: bpy.props.IntProperty(default=0)
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)


classes = [
    AudvisRealtimeItemProperties,
    AudvisRealtimeMultiProperties
]
