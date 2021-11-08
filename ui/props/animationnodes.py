import bpy


class AudvisAnimationnodesProperties(bpy.types.PropertyGroup):
    type: bpy.props.EnumProperty(name="Type", description="", items=[
        ("script", "Script",
         "Creates a Script node and an Invoke Subprogram node. Use for modifying lists and more complex use cases."),
        ("expression", "Expression", "Creates an Expression node. Use for simpler use cases.")
    ])
