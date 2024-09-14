import importlib.util
import os
import pathlib
import sys
from pathlib import Path

import bpy
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
)
from bpy.types import (
    AddonPreferences,
)

from . import install_lib
from .buttonspanel import AudVisButtonsPanel_Npanel, SequencerButtonsPanel_Update
from .realtime import input_device_options
from .. import ui


def on_npanelname_update(prefs, context):
    AudVisButtonsPanel_Npanel.bl_category = prefs.npanel_name

    # unregister
    for cls in ui.classes:
        if issubclass(cls, AudVisButtonsPanel_Npanel):
            try:
                bpy.utils.unregister_class(cls)
            except Exception as e:
                # print(e)
                pass

    # register
    for cls in ui.classes:
        if issubclass(cls, AudVisButtonsPanel_Npanel) and not issubclass(cls, SequencerButtonsPanel_Update):
            bpy.utils.register_class(cls)
    for cls in ui.classes:
        if issubclass(cls, SequencerButtonsPanel_Update):
            bpy.utils.register_class(cls)


class AudvisAddonPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = bpy._audvis_module

    npanel_name: StringProperty(
        name="Panel Category",
        default="AudVis",
        update=on_npanelname_update
    )
    pip_target: EnumProperty(name="Install directory", items=[
        ("default", "Blender", ""),
        ("addon-modules", "User Add-On Modules", ""),
    ], default="addon-modules")

    realtime_device_use_global: BoolProperty(name="Use Global Realtime Device", default=False)
    realtime_device: EnumProperty(name="Realtime Device", items=input_device_options)

    def draw(self, context):
        layout = self.layout
        layout.box().column().prop(self, "npanel_name")
        self._draw_install(context)
        layout.box().column().operator("audvis.forcereload", text="Reload AudVis")

    def _draw_writable(self, row, directory):
        p = Path(directory)
        writable = False
        if p.exists():
            writable = os.access(p, os.W_OK)
        else:
            for pp in p.parents:
                if pp.exists():
                    writable = os.access(pp, os.W_OK)
                    break
        row.label(text=directory)
        if writable:
            row.label(text="writable", icon="EXPORT")
        else:
            row.label(text="not writable!", icon="ERROR")

    def _draw_module_row(self, box, module_name, desc, uninstall, is_supported):
        col = box.column()
        row = col.row().split(factor=.4)
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            mod = importlib.import_module(module_name)
            version = "unknown"
            if hasattr(mod, "version_info"):  # mido
                version = str(mod.version_info)
            elif hasattr(mod, "__version__"):  # other
                version = mod.__version__
            # row.label(text="{} | {}: {}".format(desc, mod.__name__, version))
            row.label(text=desc)
            row.label(text=mod.__name__)
            row.label(text=version)
            mod_file = pathlib.Path(mod.__file__).absolute()
            file_exists = mod_file.exists()
            main_path = pathlib.Path(install_lib.main_path).absolute()
            if not file_exists:
                row.label(text="Uninstalled")
            elif uninstall and str(mod_file).startswith(str(main_path)):
                row.operator(uninstall,
                             text='uninstall',
                             icon='TRASH')
        else:
            row.label(text=desc + ": missing")

    def _draw_install(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column()
        col.prop(self, "realtime_device_use_global")
        if self.realtime_device_use_global:
            if bpy.audvis.is_realtime_supported():
                col.prop(self, "realtime_device")
            else:
                col.label(text="Realtime not supported. Install sounddevice first")
        col = box.column()
        col.label(text="PYTHON LIBRARIES:")
        col.label(text="AudVis needs some external python libraries. Here you can install them.", icon="INFO")
        col.prop(self, "pip_target")
        row = col.row().split(factor=.8)
        if self.pip_target == 'addon-modules':
            pth = install_lib.get_libs_path_latest()
            if pth is None:
                pth = install_lib.audvis_libs_path
            self._draw_writable(row, pth)
        elif self.pip_target == 'default':
            self._draw_writable(row, install_lib.main_path)
        col.operator("audvis.install", text="(Re)install python packages")

        self._draw_module_row(box,
                              "sounddevice",
                              "Realtime analyzer",
                              "audvis.realtime_uninstall",
                              bpy.audvis.is_realtime_supported())
        self._draw_module_row(box,
                              "cv2",
                              "Video camera",
                              "audvis.video_uninstall",
                              bpy.audvis.is_video_supported())
        self._draw_module_row(box,
                              "soundfile",
                              "Sound recording",
                              "audvis.realtime_uninstall_soundrecorder",
                              bpy.audvis.is_recording_supported())

        self._draw_module_row(box,
                              "mido",
                              "MIDI realtime analyzer",
                              None,
                              bpy.audvis.is_midi_realtime_supported())


classes = [
    AudvisAddonPreferences,
]
