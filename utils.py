import bpy


def call_ops_override(operator, override, **kwargs):
    if hasattr(bpy.context, 'temp_override'):  # blender 3.2 and higher
        with bpy.context.temp_override(**override):
            operator(**kwargs)
    else:
        operator(override, **kwargs)
