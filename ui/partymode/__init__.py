import bpy

from . import gizmo
from . import (in_window, in_workspace)
from . import party_panel


class AUDVIS_OT_Partymode(bpy.types.Operator):
    bl_idname = "audvis.partymode"
    bl_label = "Enter Party Mode"
    bl_description = "Opens full screen 3d area.\nTo exit party mode, press Alt+F4"
    party_implementation: bpy.props.StringProperty(name="Party Mode Implementation")
    override = None

    def invoke(self, context, event):
        self.party_implementation = context.scene.audvis.party.implementation
        context.window_manager.modal_handler_add(self)
        if self.party_implementation == 'workspace':
            return in_workspace.invoke(self, context, event)
        elif self.party_implementation == 'window':
            return in_window.invoke(self, context, event)

    def modal(self, context, event):
        if self.party_implementation == 'workspace':
            return in_workspace.modal(self, context, event)
        elif self.party_implementation == 'window':
            return in_window.modal(self, context, event)


def render_menuitem(self, context):
    self.layout.separator()
    self.layout.operator("audvis.partymode", text="Enter Party Mode")


def register():
    try:
        bpy.types.TOPBAR_MT_render.append(render_menuitem)
    except:
        pass


def unregister():
    try:
        bpy.types.TOPBAR_MT_render.remove(render_menuitem)
    except:
        pass


classes = gizmo.classes + [
    AUDVIS_OT_Partymode,
] + party_panel.classes
