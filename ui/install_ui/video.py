import bpy

from .. import install_lib


class AUDVIS_OT_VideoUninstall(bpy.types.Operator):
    bl_idname = "audvis.video_uninstall"
    bl_label = "Uninstall audvis video support"
    bl_description = "Uninstall needed python modules"

    def execute(self, context):
        install_lib.PipInstaller().uninstall("cv2")
        return {'FINISHED'}
