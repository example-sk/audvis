import bpy

impl_window = (
    'window',
    'Window',
    'Opens temporary window and maximizes it. Use if you want to control Blender from main window.'
)
impl_workspace = (
    'workspace',
    'Workspace',
    'Adds a workspace. Use for higher FPS.'
)

if bpy.app.version[0] < 4:
    _supported_implementations = [impl_window, impl_workspace]
else:
    _supported_implementations = [impl_workspace]


class AudvisPartyProperties(bpy.types.PropertyGroup):
    show_xray: bpy.props.BoolProperty(name="Show X-Ray for Wireframe in Party Mode", default=False)
    hide_mouse: bpy.props.BoolProperty(name="Hide Mouse Pointer", default=False)
    shading: bpy.props.EnumProperty(name="Shading in Party Mode", items=[
        ('WIREFRAME', 'Wireframe', ''),
        ('SOLID', 'Solid', ''),
        ('MATERIAL', 'Material', ''),
        ('RENDERED', 'Rendered', ''),
    ], default='RENDERED')
    implementation: bpy.props.EnumProperty(name="Implementation of Party Mode", items=_supported_implementations)
