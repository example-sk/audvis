import random
import bpy
import string
from bpy.types import Operator


class AUDVIS_OT_spectrogramAdd(Operator):
    bl_idname = "audvis.spectrogram_add"
    bl_label = "Add Spectrogram"

    def execute(self, context):
        spectrogram = context.scene.audvis.spectrograms.add()
        spectrogram.enable = True
        name = "spectrogram " + ''.join(random.choice(string.ascii_letters) for i in range(4))
        spectrogram.image = bpy.data.images.new(name=name, width=spectrogram.width, height=spectrogram.height)
        spectrogram.image.source = 'GENERATED'
        if hasattr(spectrogram.image, "use_half_precision"):
            spectrogram.image.use_half_precision = False
        spectrogram.name = spectrogram.image.name
        context.scene.audvis.spectrogram_meta.index = len(context.scene.audvis.spectrograms) - 1
        return {"FINISHED"}
