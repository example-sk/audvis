import bpy

from .. import install_lib


class AUDVIS_OT_InstallAll(bpy.types.Operator):
    bl_idname = "audvis.install"
    bl_label = "Install all libraries for AudVis"
    bl_description = "Install needed python modules"

    def execute(self, context):
        install_lib.PipInstaller().install()
        return {'FINISHED'}
