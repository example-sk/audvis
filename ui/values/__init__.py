from bpy.types import (Panel)

from . import presets
from ..buttonspanel import SequencerButtonsPanel, SequencerButtonsPanel_Npanel


def get_sample_calc(self):
    v = self.sample / 1000
    if self.value_aud.enable and self.value_aud.adsr_enable:
        v = max([
            v,
            self.value_aud.adsr_attack,
            self.value_aud.adsr_sustain,
            self.value_aud.adsr_release,
        ])
    return v


class AUDVIS_PT_values(Panel):
    bl_label = "Driver Values"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header_preset(self, _context):
        self.layout.operator("audvis.drivervalues_preset_menu", icon="PRESET", text="")

    def draw(self, context):
        self._aud_props(context)
        layout = self.layout
        if not context.scene.audvis.value_aud.enable:
            col = layout.column(align=True)
            col.prop(context.scene.audvis, "value_highpass_freq")
            col.prop(context.scene.audvis, "value_highpass_factor")
        col = layout.column(align=True)
        # col.prop(context.scene.audvis, "value_logarithm")
        col.prop(context.scene.audvis, "value_factor")
        col.prop(context.scene.audvis, "value_max")
        col.prop(context.scene.audvis, "value_add")
        col.prop(context.scene.audvis, "value_noise")

        col = layout.column(align=True)
        col.prop(context.scene.audvis, "value_normalize")
        if context.scene.audvis.value_normalize == 'max':
            col.prop(context.scene.audvis, "value_normalize_clamp_to")

        col = layout.column(align=True)
        col.prop(context.scene.audvis, "value_fadeout_type")
        if context.scene.audvis.value_fadeout_type != 'off':
            col.prop(context.scene.audvis, "value_fadeout_speed")

    def _aud_props(self, context):
        col = self.layout.column(align=True)
        props = context.scene.audvis.value_aud
        col.prop(props, "enable")
        if props.enable:
            col = col.box().column(align=True)
            col.prop(props, "highpass")
            col.prop(props, "highpass_factor")
            col.prop(props, "lowpass")
            col.prop(props, "lowpass_factor")
            col.prop(props, "use_fake_curve_light")
            if props.use_fake_curve_light and props.fake_curve_light is not None:
                col.template_curve_mapping(props.fake_curve_light, 'falloff_curve')

            # col.prop(props, "env_enable")
            # if props.env_enable:
            #     col.prop(props, "env_attack")
            #     col.prop(props, "env_release")
            #     col.prop(props, "env_threshold")
            #     col.prop(props, "env_arthreshold")

            col.prop(props, "adsr_enable")
            if props.adsr_enable:
                col.prop(props, "adsr_attack")
                col.prop(props, "adsr_decay")
                col.prop(props, "adsr_sustain")
                col.prop(props, "adsr_release")


class AUDVIS_PT_valuesScene(AUDVIS_PT_values, SequencerButtonsPanel):
    bl_parent_id = "AUDVIS_PT_audvisScene"


class AUDVIS_PT_valuesNpanel(AUDVIS_PT_values, SequencerButtonsPanel_Npanel):
    pass


classes = presets.classes + [
    AUDVIS_PT_valuesScene,
    AUDVIS_PT_valuesNpanel,
]
