from bpy.types import Operator


class AUDVIS_OT_spectrogramRemove(Operator):
    bl_idname = "audvis.spectrogram_remove"
    bl_label = "Remove Spectrogram"

    @classmethod
    def poll(cls, context):
        return context.scene.audvis.spectrogram_meta.index < len(context.scene.audvis.spectrograms)

    def execute(self, context):
        audvis_props = context.scene.audvis
        index = audvis_props.spectrogram_meta.index
        # spect_props = audvis_props.spectrograms[index]
        audvis_props.spectrograms.remove(index)
        if len(audvis_props.spectrograms) == 0:
            audvis_props.spectrogram_meta.index = 0
        elif index >= len(audvis_props.spectrograms):
            audvis_props.spectrogram_meta.index = len(audvis_props.spectrograms) - 1
        return {"FINISHED"}
