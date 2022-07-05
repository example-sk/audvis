from bpy.types import Operator


class AUDVIS_OT_spectrogramDuplicate(Operator):
    bl_idname = "audvis.spectrogram_duplicate"
    bl_label = "Duplicate Spectrogram"

    @classmethod
    def poll(cls, context):
        return context.scene.audvis.spectrogram_meta.index < len(context.scene.audvis.spectrograms)

    def execute(self, context):
        old_spectrogram = context.scene.audvis.spectrograms[context.scene.audvis.spectrogram_meta.index]
        new_spectrogram = context.scene.audvis.spectrograms.add()
        for key, value in list(old_spectrogram.items()):
            setattr(new_spectrogram, key, getattr(old_spectrogram, key))
        new_spectrogram.image = new_spectrogram.image.copy()
        new_spectrogram.name = new_spectrogram.image.name
        context.scene.audvis.spectrogram_meta.index = len(context.scene.audvis.spectrograms) - 1
        return {"FINISHED"}
