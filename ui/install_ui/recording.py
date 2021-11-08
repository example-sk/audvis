import bpy

from .. import install_lib


class AUDVIS_OT_RealtimeUninstallSoundRecorder(bpy.types.Operator):
    bl_idname = "audvis.realtime_uninstall_soundrecorder"
    bl_label = "Uninstall audvis sound recording support"
    bl_description = "Uninstall needed python modules"

    def execute(self, context):
        install_lib.PipInstaller().uninstall("recorder")
        return {'FINISHED'}
