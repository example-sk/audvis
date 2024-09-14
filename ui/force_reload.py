import sys

import bpy


class AUDVIS_OT_ForceReload(bpy.types.Operator):
    bl_idname = "audvis.forcereload"
    bl_label = "AudVis Force Reload"

    def execute(self, context):
        # this looks horrible, but it doesn't work if executed just once
        bpy.ops.preferences.addon_refresh()
        sys.modules[bpy.audvis._module_name].unregister()
        sys.modules[bpy.audvis._module_name].register()
        bpy.ops.preferences.addon_refresh()
        sys.modules[bpy.audvis._module_name].unregister()
        sys.modules[bpy.audvis._module_name].register()
        bpy.ops.preferences.addon_refresh()
        return {"CANCELLED"}  # FINISHED causes crash


classes = [AUDVIS_OT_ForceReload, ]
