from bpy.types import Operator
import bpy


class AUDVIS_OT_spectrogramSingleToMulti(Operator):
    bl_idname = "audvis.spectrogram_single_to_multi"
    bl_label = "Copy Single Spectrogram Settings into Multi"

    def execute(self, context):
        old_spectrogram = context.scene.audvis.spectrogram
        new_spectrogram = context.scene.audvis.spectrograms.add()
        name = "copy of single spectrogram"
        for key, value in list(old_spectrogram.items()):
            setattr(new_spectrogram, key, getattr(old_spectrogram, key))
        if old_spectrogram.image:
            new_spectrogram.image = new_spectrogram.image.copy()
            new_spectrogram.name = new_spectrogram.image.name
        else:
            spectrogram = new_spectrogram
            spectrogram.image = bpy.data.images.new(name=name, width=spectrogram.width, height=spectrogram.height)
            spectrogram.image.source = 'GENERATED'
            if hasattr(spectrogram.image, "use_half_precision"):
                spectrogram.image.use_half_precision = False
            spectrogram.name = spectrogram.image.name

        context.scene.audvis.spectrogram_meta.index = len(context.scene.audvis.spectrograms) - 1
        context.scene.audvis.spectrogram_meta.mode = 'multi'
        return {"FINISHED"}
