import re
import token
from io import BytesIO
from tokenize import tokenize

import bpy
from bpy.types import Menu

from .expression_builder import build_expression


def parse_path(path):
    g = tokenize(BytesIO(path.encode("utf-8")).readline)
    tokens = [item.string for item in g if (item.string and item.type != token.ENCODING)]
    if tokens[-1] == ']':
        return "".join(tokens[:-3]), "".join(tokens[-3:])
    else:
        return "".join(tokens[:-2]), tokens[-1]


class AUDVIS_OT_button_spread_driver(bpy.types.Operator):
    """Right click entry test"""
    bl_idname = "audvis.button_spread_driver"
    bl_label = "AudVis: Spread Drivers"

    @classmethod
    def poll(cls, context):
        return bpy.ops.ui.copy_data_path_button.poll() and bpy.ops.anim.driver_button_add.poll()

    def _get_path(self, context):
        clipboard_old = context.window_manager.clipboard
        bpy.ops.ui.copy_data_path_button(full_path=True)
        full_path = context.window_manager.clipboard
        context.window_manager.clipboard = clipboard_old
        return full_path  # , property_path

    def execute(self, context):
        # pointer = getattr(context, "button_pointer", None)
        # prop = getattr(context, "button_prop", None)
        # operator = getattr(context, "button_operator", None)
        orig_path = self._get_path(context)
        index = -1
        match = re.match(r'^(.*)\[([0-9]+)\]$', orig_path)
        path = orig_path
        if match is not None:
            path = match.group(1)
            index = int(match.group(2))
        path_to_struct, property_path = parse_path(path)
        struct = eval(path_to_struct)
        fcurve = struct.driver_add(property_path, index)
        props = context.scene.audvis.spreaddrivers

        old_value = eval(orig_path)
        fcurve.driver.expression = build_expression(props, old_value)
        props.iteration += 1
        return {'FINISHED'}


# This class has to be exactly named like that to insert an entry in the right click menu
class WM_MT_button_context(Menu):
    bl_label = "Unused"

    def draw(self, context):
        pass


def menu_func(self, context):
    if bpy.ops.audvis.button_spread_driver.poll():
        layout = self.layout
        layout.separator()
        layout.operator(AUDVIS_OT_button_spread_driver.bl_idname)


classes = [
    AUDVIS_OT_button_spread_driver,
    WM_MT_button_context,
]
