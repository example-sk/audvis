import sys

import bpy

import bge


def update_callback(camera):
    # TODO: choose update method
    if False:  # trigger bpy scene update
        bpy.context.scene.frame_set((bpy.context.scene.frame_current + 1) % 10000 + 1)
    else:  # only call audvis updates
        bpy.audvis.update_data(bpy.context.scene, force=True)


class CommonClass(bge.types.KX_PythonComponent):
    def start(self, args):
        if update_callback not in self.object.scene.pre_draw_setup:
            self.object.scene.pre_draw_setup.append(update_callback)
        self.driver = bpy.audvis.driver
        if hasattr(self, "_start"):
            self._start(args)

    def update(self):
        pass
