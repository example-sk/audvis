import bpy
from bpy.types import (Operator, Menu)


class _presets:
    def _props(self):
        return self._scene().audvis

    def _scene(self):
        return bpy.context.scene

    def _common(self):
        props = self._props()
        props.factor = 1
        props.max = 100
        props.add = 0
        props.noise = 0

    def default(self):
        self._common()
        props = self._props()
        props.value_aud.enable = False
        props.value_highpass_freq = 1000
        props.value_highpass_factor = 0

    def smooth(self):
        props = self._props()
        props.value_aud.enable = True
        props.value_aud.adsr_attack = .2
        props.value_aud.adsr_decay = .2
        props.value_aud.adsr_sustain = .2
        props.value_aud.adsr_release = .2
        self._common()

    def highpass_on(self):
        props = self._props()
        props.value_aud.highpass = 300
        props.value_aud.highpass_factor = .5
        props.value_highpass_freq = 1000
        props.value_highpass_factor = 1

    def highpass_off(self):
        props = self._props()
        props.value_aud.highpass = 0
        props.value_aud.highpass_factor = .5
        props.value_highpass_freq = 1000
        props.value_highpass_factor = 0


class AUDVIS_OT_valuespresetmenu(Operator):
    bl_label = "Driver Values Presets"
    bl_idname = "audvis.drivervalues_preset_menu"

    def execute(self, context):
        bpy.ops.wm.call_menu(name="AUDVIS_MT_valuespreset")
        return {'FINISHED'}


class AUDVIS_OT_valuespreset(Operator):
    bl_label = "Driver Values Presets"
    bl_idname = "audvis.drivervalues_preset_exec"

    preset_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        obj = _presets()
        getattr(obj, self.preset_name)()
        return {'FINISHED'}


class AUDVIS_MT_valuespreset(Menu):
    bl_idname = "AUDVIS_MT_valuespreset"
    bl_label = "Driver Values Presets"

    def draw(self, _context):
        for preset_name in dir(_presets):
            if not preset_name.startswith("_"):
                self.layout.operator("audvis.drivervalues_preset_exec", text=preset_name.replace("_", " ").title()).preset_name = preset_name

    def draw_mainmenu(self, _context):  # static
        self.layout.menu("AUDVIS_MT_valuespreset")


classes = [
    AUDVIS_MT_valuespreset,
    AUDVIS_OT_valuespreset,
    AUDVIS_OT_valuespresetmenu,
]
