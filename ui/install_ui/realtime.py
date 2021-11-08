import bpy

from .. import install_lib


class AUDVIS_OT_RealtimeUninstall(bpy.types.Operator):
    bl_idname = "audvis.realtime_uninstall"
    bl_label = "Uninstall audvis realtime support"
    bl_description = "Install needed python modules"

    def execute(self, context):
        install_lib.PipInstaller().uninstall("sd")
        return {'FINISHED'}
