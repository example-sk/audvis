import sys

import bpy

from ..buttonspanel import AudVisButtonsPanel_Npanel


class AUDVIS_PT_videoNpanel(AudVisButtonsPanel_Npanel):
    bl_label = "Video Capture"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        self.layout.prop(context.scene.audvis, "video_webcam_enable", text="")

    def draw(self, context):
        col = self.layout.column(align=True)
        # col.enabled = context.scene.audvis.realtime_enable
        supported = sys.modules['audvis'].audvis.is_video_supported()
        if supported:
            col.prop(context.scene.audvis, "video_webcam_index")
            if context.scene.audvis.video_webcam_enable:
                col.prop(context.scene.audvis, "video_image")
            col.prop(context.scene.audvis, "video_tmppath")
            col.prop(context.scene.audvis, "video_image_flip_horizontal")
            col = self.layout.column(align=True)
            col.prop(context.scene.audvis, "video_resize")
            if context.scene.audvis.video_resize:
                col.prop(context.scene.audvis, "video_resize_relative")
                if context.scene.audvis.video_resize_relative:
                    col.prop(context.scene.audvis, "video_resize_ratio")
                else:
                    col.prop(context.scene.audvis, "video_width")
                    col.prop(context.scene.audvis, "video_height")
            self._draw_contour(context)
        else:
            col.label(text="Video not supported. Install opencv first:")
            col.operator("audvis.install", text="Install python packages")
        err = sys.modules['audvis'].audvis.get_video_error()
        if err:
            col = self.layout.column(align=True)
            col.label(text="Error: " + err)

    def _draw_contour(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.audvis, "video_contour_enable")
        if context.scene.audvis.video_contour_enable:
            # col.prop(context.scene.audvis, "video_contour_object_type") # TODO: curve and mesh are useless for now...
            col.prop(context.scene.audvis, "video_contour_chain_approx")
            col.prop(context.scene.audvis, "video_contour_threshold")
            col.prop(context.scene.audvis, "video_contour_simplify")
            col.prop(context.scene.audvis, "video_contour_min_points_per_stroke")
            col.prop(context.scene.audvis, "video_contour_size")


def on_blendfile_loaded():
    if hasattr(bpy.context, "scene"):
        img = bpy.context.scene.audvis.video_image
        if img is not None and hasattr(img, "pixels") and len(img.pixels) == 0:
            img.source = 'GENERATED'
            img.scale(100, 100)


def on_blendfile_save():
    pass


def unregister():
    try:
        sys.modules['audvis'].audvis.video_analyzer.kill()
        sys.modules['audvis'].audvis.video_analyzer = None
    except:
        pass


classes = [
    AUDVIS_PT_videoNpanel,
]
