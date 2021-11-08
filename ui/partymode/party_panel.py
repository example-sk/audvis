from bpy.types import (Panel)

from ..buttonspanel import (SequencerButtonsPanel, SequencerButtonsPanel_Npanel)


class AUDVIS_PT_partymode(Panel):
    bl_label = "Party Mode"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        props = context.scene.audvis.party
        col = self.layout.column(align=True)
        col.prop(props, "implementation")
        col.prop(props, "shading")
        col.prop(props, "hide_mouse")
        if props.shading == 'WIREFRAME':
            col.prop(props, "show_xray")
        col.operator("audvis.partymode", text="Enter Party Mode", icon='FULLSCREEN_ENTER')
        col.label(text="Note: Press ESC to end the Party Mode")
        if props.shading != 'RENDERED':
            col = self.layout.column(align=True)
            col.label(text="For more settings see")
            col.label(text="Blender Preferences -> Themes")
            col.prop(context.preferences.themes[0].view_3d.space.gradients, "high_gradient")
            col.operator("preferences.reset_default_theme")


class AUDVIS_PT_partymodeScene(AUDVIS_PT_partymode, SequencerButtonsPanel):
    bl_parent_id = "AUDVIS_PT_audvisScene"


class AUDVIS_PT_partymodeNpanel(AUDVIS_PT_partymode, SequencerButtonsPanel_Npanel):
    pass


classes = [
    AUDVIS_PT_partymodeNpanel,
    AUDVIS_PT_partymodeScene,
]
