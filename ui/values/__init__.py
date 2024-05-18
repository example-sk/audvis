from . import presets
from ..buttonspanel import AudVisButtonsPanel_Npanel


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


class AUDVIS_PT_valuesNpanel(AudVisButtonsPanel_Npanel):
    bl_label = "Driver Values"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header_preset(self, _context):
        self.layout.operator("audvis.drivervalues_preset_menu", icon="PRESET", text="")

    def draw(self, context):
        self._aud_props(context)
        props = context.scene.audvis
        layout = self.layout
        if not props.value_aud.enable:
            col = layout.column(align=True)
            col.prop(props, "value_highpass_freq")
            col.prop(props, "value_highpass_factor")
        col = layout.column(align=True)
        # col.prop(props, "value_logarithm")
        col.prop(props, "value_factor")
        col.prop(props, "value_max")
        col.prop(props, "value_add")
        col.prop(props, "value_noise")

        col = layout.column(align=True)
        row = col.row()
        row.label(text="Normalize Value")
        row.prop(props, "value_normalize", text="")
        if props.value_normalize == 'max':
            col.prop(props, "value_normalize_clamp_to")

        col = layout.column(align=True)
        row = col.row()
        row.label(text="Fade Out Type")
        row.prop(props, "value_fadeout_type", text="")
        if props.value_fadeout_type != 'off':
            col.prop(props, "value_fadeout_speed")
        row = col.row()
        row.label(text="Additive Type")
        row.prop(props, "value_additive_type", text="")
        if props.value_additive_type != 'off':
            col.prop(props, "value_additive_reset")
        if props.value_additive_type != 'off' or props.value_fadeout_type != 'off':
            col.label(text="Warning: Fadeout (a little bit)")
            col.label(text="and Additive (a lot)")
            col.label(text="can cause inconsistent state")
            col.label(text="if you skip frames.")
            col.label(text="Maybe you want to bake drivers")
            col.label(text="before rendering.")

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


classes = presets.classes + [
    AUDVIS_PT_valuesNpanel,
]
