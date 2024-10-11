import bpy

from .. import install_lib


class AUDVIS_OT_InstallAll(bpy.types.Operator):
    bl_idname = "audvis.install"
    bl_label = "Install all libraries for AudVis"
    bl_description = "Install needed python modules"

    @classmethod
    def poll(cls, context):
        return not bpy._audvis_module.startswith("bl_ext.")

    def execute(self, context):
        install_lib.PipInstaller().install()
        return {'FINISHED'}
