import bpy
from bpy.types import Panel

from . import bge_logic_create, bge_register_component

options = [
    ('audvis.bge.Updater', "Updater", "Only updates (if you don't use any other AudVis components anywhere)"),
    ('audvis.bge.Realtime', "Realtime Sound", "Set property value from realtime sound driver"),
    ('audvis.bge.MidiRealtime', "Midi Realtime", "Set property value from realtime sound driver"),
]


class AUDVIS_PT_Bge(Panel):
    bl_space_type = 'LOGIC_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Logic"
    bl_label = "AudVis"

    @classmethod
    def poll(cls, context):
        return len(dir(bpy.ops.logic))

    def draw(self, context):
        box = self.layout.box()
        box.label(text="Logic Setup:")
        box.operator('audvis.bge_logic_create')

        box = self.layout.box()
        box.label(text="Register Component:")
        for item in options:
            col = box.column()
            col.label(text=item[2])
            col.operator('audvis.bge_register_component', text=item[1]).component = item[0]


classes = [
    bge_register_component.AUDVIS_OT_BgeRegisterComponent,
    bge_logic_create.AUDVIS_OT_BgeLogicCreate,
    AUDVIS_PT_Bge,
]
