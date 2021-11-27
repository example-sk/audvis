import glob
import os

import bpy
from bpy.types import (
    Operator,
)


# TODO: self.report({'INFO'},"This ma take some time")

class AUDVIS_OT_spectrogrambake(Operator):
    bl_idname = "audvis.spectrogram_bake"
    bl_label = "Bake Spectrogram"
    bl_description = "Exports the image sequence"

    return_frame = -1
    cur_frame = -1
    end_frame = -1
    timer = None
    obj = None

    @classmethod
    def poll(self, context):
        if not context.scene.audvis.spectrogram.enable:
            return False
        if not bpy.data.is_saved:
            return False
        return True

    def invoke(self, context, event):
        scene = context.scene
        bpy.ops.screen.animation_cancel()
        self.return_frame = scene.frame_current
        self.cur_frame = scene.frame_start
        self.end_frame = scene.frame_end
        context.scene.frame_set(self.cur_frame)
        self.timer = context.window_manager.event_timer_add(.0000001, window=context.window)
        # context.window_manager.progress_begin(scene.frame_start, scene.frame_end)
        context.workspace.status_text_set("AudVis: Baking Shape Modifier")
        context.window_manager.modal_handler_add(self)
        self.clear_old_data(context)
        return {'RUNNING_MODAL'}

    def clear_old_data(self, context):
        pattern = os.path.join(bpy.path.abspath(context.scene.audvis.spectrogram.bake_path), 'audvis-spect-*.png')
        for file in glob.glob(pattern):
            os.unlink(file)

    def modal(self, context, event):
        if event.type == 'TIMER':
            context.scene.frame_set(self.cur_frame)
            if context.scene.audvis.spectrogram.mode in ('rolling', 'snapshot'):
                f = os.path.join(bpy.path.abspath(context.scene.audvis.spectrogram.bake_path),
                                 'audvis-spect-%04d.png' % self.cur_frame)  # TODO!!!
                bpy.data.images['AudVis Spectrogram'].save_render(filepath=f)
            elif context.scene.audvis.spectrogram.mode == 'one-big':
                pass

            # context.window_manager.progress_update(self.cur_frame)
            start = context.scene.frame_start
            perc = int(((self.cur_frame - start) / (self.end_frame - start)) * 100)
            context.workspace.status_text_set("AudVis: Baking Spectrogram: {}%".format(perc))
            if self.cur_frame >= self.end_frame:
                self._end(context)
                return {'FINISHED'}
            self.cur_frame += 1
            return {'PASS_THROUGH'}
        elif event.type == 'ESC':
            self._end(context)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def _end(self, context):
        if context.scene.audvis.spectrogram.mode == 'one-big':
            f = os.path.join(bpy.path.abspath(context.scene.audvis.spectrogram.bake_path),
                             "audvis-spect.png")
            bpy.data.images['AudVis Spectrogram'].save_render(filepath=f)
        context.scene.audvis.spectrogram.enable = False
        context.scene.frame_set(self.return_frame)
        context.window_manager.event_timer_remove(self.timer)
        # context.window_manager.progress_end()
        context.workspace.status_text_set(None)


classes = [
    AUDVIS_OT_spectrogrambake,
]
