import glob
import os

import bpy
from bpy.types import (
    Operator,
)


# TODO: self.report({'INFO'},"This ma take some time")

class AUDVIS_OT_spectrogrambake(Operator):
    bl_idname = "audvis.spectrogram_bake"
    bl_label = "Bake Spectrograms"
    bl_description = "Exports the image sequence"

    return_frame = -1
    cur_frame = -1
    start_frame = -1
    end_frame = -1
    timer = None
    obj = None

    dirname: bpy.props.StringProperty(name="Output Directory", subtype="DIR_PATH", default="//audvis-spectrogram/")
    use_subdirs: bpy.props.BoolProperty(name="Use Subdirectories for Each Image", default=True)
    disable_after_bake: bpy.props.BoolProperty(name="Disable After Baking", default=True,
                                               description="Disable spectrogram after end of baking process")
    show_directory: bpy.props.BoolProperty(name="Show Directory", default=True)

    @classmethod
    def poll(self, context):
        return True

    def invoke(self, context, event):
        self.dirname = context.scene.audvis.spectrogram_meta.last_dirname
        self.use_subdirs = context.scene.audvis.spectrogram_meta.last_use_subdirs
        self.disable_after_bake = context.scene.audvis.spectrogram_meta.last_disable_after_bake
        return context.window_manager.invoke_props_dialog(self)

    # def clear_old_data(self, context):
    #     pattern = os.path.join(bpy.path.abspath(self.dirname), 'audvis-spect-*.png')
    #     for file in glob.glob(pattern):
    #         os.unlink(file)

    def draw(self, context):
        col = self.layout.column()
        col.prop(self, 'dirname')
        col.prop(self, 'use_subdirs')
        col.prop(self, 'disable_after_bake')
        col.prop(self, 'show_directory')
        col = self.layout.column()
        col.alert = True
        col.label(text="After baking, you have to load the image")
        col.label(text="sequence manually where needed.")

    def modal(self, context, event):
        if event.type == 'TIMER':
            context.scene.frame_set(self.cur_frame)
            for spect_props in self._get_all_spect_props(context):
                if spect_props.mode in ('rolling', 'snapshot'):
                    image = spect_props.image
                    self._save_image(image, self.cur_frame)
                elif spect_props.mode == 'one-big':
                    pass

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
        for spect_props in self._get_all_spect_props(context):
            if spect_props.mode == 'one-big':
                image = spect_props.image
                self._save_image(image)
        if self.disable_after_bake:
            if context.scene.audvis.spectrogram_meta.mode == 'single':
                context.scene.audvis.spectrogram.enable = False
            elif context.scene.audvis.spectrogram_meta.mode == 'multi':
                context.scene.audvis.spectrogram_meta.enable = False
        context.scene.frame_set(self.return_frame)
        context.window_manager.event_timer_remove(self.timer)
        self.timer = None
        context.workspace.status_text_set(None)

    def _save_image(self, image, index=None):
        dirname = bpy.path.abspath(self.dirname)
        if self.use_subdirs:
            dirname = os.path.join(dirname, image.name)
        image_name = image.name
        if index is not None:
            image_name = image_name + ("-%05d" % index)
        ext = None
        #  https://docs.blender.org/api/current/bpy.types.Image.html?highlight=file_format#bpy.types.Image.file_format
        if image.file_format in ('TARGA', 'TARGA_RAW'):
            ext = 'tga'
        elif image.file_format in ('JPEG', 'JPEG2000'):
            ext = 'jpg'
        elif image.file_format in ('OPEN_EXR', 'OPEN_EXR_MULTILAYER'):
            ext = 'exr'
        elif image.file_format in ('CINEON',):
            ext = 'cin'
        else:  # if image.file_format in ('PNG', 'BMP', 'IRIS', 'DPX', 'TIFF', 'WEBP'):
            ext = image.file_format.lower()
        f = os.path.join(dirname, image_name + "." + ext)
        image.filepath_raw = f
        os.makedirs(os.path.dirname(f), exist_ok=True)
        image.save()

    def _show_directory(self):
        import sys
        import subprocess
        abs_dir = bpy.path.abspath(self.dirname)
        os.makedirs(abs_dir, exist_ok=True)

        if sys.platform == 'darwin':
            subprocess.check_call(['open', '--', abs_dir])
        elif sys.platform.startswith('linux'):
            subprocess.check_call(['xdg-open', abs_dir])
        elif sys.platform == 'win32':
            subprocess.check_call(['explorer', abs_dir])

    def execute(self, context):
        if self.show_directory:
            self._show_directory()
        context.scene.audvis.spectrogram_meta.last_dirname = self.dirname
        context.scene.audvis.spectrogram_meta.last_use_subdirs = self.use_subdirs
        context.scene.audvis.spectrogram_meta.last_disable_after_bake = self.disable_after_bake
        scene = context.scene
        bpy.ops.screen.animation_cancel()
        self.return_frame = scene.frame_current
        self.start_frame = scene.frame_start
        self.cur_frame = self.start_frame
        self.end_frame = scene.frame_end
        context.scene.frame_set(self.start_frame)
        self.timer = context.window_manager.event_timer_add(.0000001, window=context.window)
        context.workspace.status_text_set("AudVis: Baking Shape Modifier")
        context.window_manager.modal_handler_add(self)
        # self.clear_old_data(context)
        return {'RUNNING_MODAL'}

    def _get_all_spect_props(self, context):
        scene = context.scene
        if scene.audvis.spectrogram_meta.mode == 'single':
            if scene.audvis.spectrogram.enable:
                if scene.audvis.spectrogram.image is None:
                    from audvis import audvis
                    audvis.spectrogram_generator.modify(bpy.context.scene)
                return [scene.audvis.spectrogram]
            return []
        elif scene.audvis.spectrogram_meta.mode == 'multi':
            if scene.audvis.spectrogram_meta.enable:
                return [sp for sp in scene.audvis.spectrograms if sp.enable]
            return []


classes = [
    AUDVIS_OT_spectrogrambake,
]
