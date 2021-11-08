import bpy


class AudvisPartyProperties(bpy.types.PropertyGroup):
    show_xray: bpy.props.BoolProperty(name="Show X-Ray for Wireframe in Party Mode", default=False)
    hide_mouse: bpy.props.BoolProperty(name="Hide Mouse Pointer", default=False)
    shading: bpy.props.EnumProperty(name="Shading in Party Mode", items=[
        ('WIREFRAME', 'Wireframe', ''),
        ('SOLID', 'Solid', ''),
        ('MATERIAL', 'Material', ''),
        ('RENDERED', 'Rendered', ''),
    ], default='RENDERED')
    implementation: bpy.props.EnumProperty(name="Implementation of Party Mode", items=[
        ('window', 'Window',
         'Opens temporary window and maximizes it. Use if you want to control Blender from main window.'),
        ('workspace', 'Workspace', 'Adds a workspace. Use for higher FPS.'),
    ])
