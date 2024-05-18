import bpy
import os
from bpy.types import Menu

from .buttonspanel import AudVisButtonsPanel_Npanel


class AUDVIS_MT_scripttemplates(Menu):
    bl_idname = "AUDVIS_MT_scripttemplates"
    bl_label = "AudVis Script Templates"

    def draw(self, _context):
        self.path_menu(
            [os.path.join(os.path.dirname(os.path.dirname(__file__)), "doc", "scripts")],
            "text.open",
            props_default={"internal": True},
        )

    def draw_mainmenu(self, _context):  # static
        self.layout.menu("AUDVIS_MT_scripttemplates")


class AUDVIS_OT_scriptmenuopen(bpy.types.Operator):
    bl_idname = "audvis.scriptmenuopen"
    bl_label = "AudVis Script Template"

    def execute(self, context):
        bpy.ops.wm.call_menu(name="AUDVIS_MT_scripttemplates")
        return {"FINISHED"}


class AUDVIS_PT_examplescriptsNpanel(AudVisButtonsPanel_Npanel):
    bl_label = "Script Templates"

    scriptlist = None

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        col = self.layout.column(align=True)
        col.label(text="Please Switch to")
        col.label(text="Scripting Workspace")
        col.operator("audvis.scriptmenuopen", text="Choose Script Template")


def register():
    if hasattr(bpy.types, 'TEXT_MT_templates'):
        bpy.types.TEXT_MT_templates.append(AUDVIS_MT_scripttemplates.draw_mainmenu)


def unregister():
    if hasattr(bpy.types, 'TEXT_MT_templates'):
        bpy.types.TEXT_MT_templates.remove(AUDVIS_MT_scripttemplates.draw_mainmenu)


classes = [
    AUDVIS_PT_examplescriptsNpanel,
    AUDVIS_MT_scripttemplates,
    AUDVIS_OT_scriptmenuopen
]
