# -*- coding: utf-8 -*-
import importlib
import sys

bl_info = {
    "name": "AudVis - audio visualization driver",
    "author": "example.sk",
    "version": (7, 0, 1),
    "blender": (2, 80, 0),
    "location": "View 3D > Sidebar > AudVis Tab",
    "description": (
        "Tools for awesome audio visualizations. You can use Sequence Analyzer to render a music video, or Realtime Analyzer combined with Party Mode to impress people on your party."),
    "wiki_url": "https://example.sk/audvis/",
    "category": "Animation"}

import bpy
from bpy.app.handlers import persistent

bpy._audvis_module = __package__

from . import scripting
from . import ui
from .ui import install_lib
from .audvis_class import AudVis

classes = ui.classes + scripting.classes

is_first_load = True


def _reload_modules():
    for key in list(sys.modules.keys()):
        if key.startswith("audvis"):
            importlib.reload(sys.modules[key])


def register2():
    global is_first_load
    global audvis
    global register_script
    global classes

    if is_first_load:
        is_first_load = False
    else:
        for i in range(2):  # just to be sure...
            _reload_modules()

    audvis = AudVis()
    bpy.audvis = audvis
    audvis._module_name = __package__
    register_script = audvis.register_script
    classes = ui.classes + scripting.classes
    for c in classes:
        try:
            bpy.utils.register_class(c)
        except:
            pass


def unregister2():
    for c in reversed(classes):
        try:
            bpy.utils.unregister_class(c)
        except:
            pass


@persistent
def load_handler(dummy):
    bpy.app.driver_namespace['audvis'] = audvis.driver
    if audvis.update_data not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(audvis.update_data)
        # bpy.app.handlers.frame_change_pre.append(audvis.profiled_update_data)
    if save_pre_handler not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(save_pre_handler)
    ui.on_blendfile_loaded()


@persistent
def unload_handler(dummy):
    audvis.reload()


def save_pre_handler(dummy):
    ui.on_blendfile_save()


def register():
    register_syspath()
    register2()
    ui.register()
    bpy.app.handlers.load_post.append(load_handler)
    bpy.app.handlers.load_pre.append(unload_handler)
    register_keymaps()
    load_handler(None)


def register_syspath():
    path = install_lib.get_libs_path_latest()
    if path is None:
        return
    unregister_syspath()
    sys.path.append(path)


def unregister_syspath():
    lst = [d for d in sys.path if d.startswith(install_lib.audvis_libs_path)]
    for d in lst:
        sys.path.remove(d)


def unregister():
    global audvis
    unregister_syspath()  # probably useless
    unregister_keymaps()
    unregister2()
    ui.unregister()
    bpy.app.handlers.frame_change_pre.remove(audvis.update_data)
    bpy.app.handlers.load_post.remove(load_handler)
    bpy.app.handlers.save_pre.remove(save_pre_handler)
    bpy.app.driver_namespace.pop('audvis')
    audvis = None
    bpy.audvis = None


### keymaps
addon_keymaps = []


def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # region_type in  ('WINDOW', 'HEADER', 'CHANNELS', 'TEMPORARY', 'UI', 'TOOLS', 'TOOL_PROPS',
        # 'PREVIEW', 'HUD', 'NAVIGATION_BAR', 'EXECUTE', 'FOOTER', 'TOOL_HEADER')
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("audvis.partymodeclose", "ESC", "PRESS")
        addon_keymaps.append((km, kmi))


def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
