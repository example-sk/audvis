import sys

import bpy


class AUDVIS_OT_ForceReload(bpy.types.Operator):
    bl_idname = "audvis.forcereload"
    bl_label = "AudVis Force Reload"

    def execute(self, context):
        # unregister() sets bpy.audvis to None, so resolve the module once up front
        module_name = getattr(bpy, "_audvis_module", None)
        module = sys.modules.get(module_name) if module_name else None
        if module is None:
            self.report({'WARNING'}, "AudVis module not loaded, nothing to reload")
            return {"CANCELLED"}
        # this looks horrible, but it doesn't work if executed just once
        bpy.ops.preferences.addon_refresh()
        module.unregister()
        module.register()
        bpy.ops.preferences.addon_refresh()
        module.unregister()
        module.register()
        bpy.ops.preferences.addon_refresh()
        return {"CANCELLED"}  # FINISHED causes crash


classes = [AUDVIS_OT_ForceReload, ]
