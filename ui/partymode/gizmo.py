import bpy

partymode_windows = []  # injected from open window operator

from bpy.types import (
    GizmoGroup,
)


def is_party_mode(context):
    # return True
    if context.scene.audvis.party.implementation == 'workspace':
        return context.workspace.name.startswith('audvis-party')
    return context.window in partymode_windows


class AUDVIS_OT_PartymodeClose(bpy.types.Operator):
    bl_idname = "audvis.partymodeclose"
    bl_label = "Close the Party Mode Window"
    bl_description = bl_label

    @classmethod
    def poll(self, context):
        return is_party_mode(context)

    def invoke(self, context, event):
        if context.scene.audvis.party.implementation == 'workspace':
            if context.workspace.name.startswith('audvis-party'):
                self._close_workspace(context)
        else:
            if context.window in partymode_windows:
                partymode_windows.remove(context.window)
                bpy.ops.wm.window_close()
        return {'FINISHED'}

    def _close_workspace(self, context):
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()
        bpy.ops.wm.window_fullscreen_toggle()
        bpy.ops.screen.screen_full_area(use_hide_panels=True)
        workspace = context.workspace
        bpy.ops.screen.workspace_cycle('INVOKE_DEFAULT')
        bpy.ops.workspace.delete({'workspace': workspace})


class AUDVIS_partymode_gizmogroup(GizmoGroup):
    bl_idname = "AUDVIS_partymode_gizmogroup"
    bl_label = "AudVis Party Mode Gizmo Group"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'}

    @classmethod
    def setup_keymap(cls, keyconfig):
        keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new('audvis_partymode_gizmo')
        keymap.keymap_items.new('audvis.partymodeclose', 'LEFTMOUSE', 'CLICK')
        return keymap

    @classmethod
    def poll(cls, context):
        is_party = is_party_mode(context)
        return not bpy.context.screen.is_animation_playing and is_party

    def draw_prepare(self, context):
        region = context.region
        self.close_gizmo.matrix_basis[0][3] = region.width - 40  # left
        self.close_gizmo.matrix_basis[1][3] = 40  # bottom

    def setup(self, context):
        mpr = self.gizmos.new("GIZMO_GT_button_2d")  # This line crashes Blender
        mpr.icon = 'PANEL_CLOSE'
        mpr.draw_options = {'BACKDROP', 'OUTLINE'}
        mpr.target_set_operator('audvis.partymodeclose')

        mpr.alpha = 0.2
        mpr.color_highlight = 0.8, 0.8, 0.8
        mpr.alpha_highlight = .8

        mpr.scale_basis = (80 * 0.35) / 2  # Same as buttons defined in C
        self.close_gizmo = mpr


classes = [
    AUDVIS_OT_PartymodeClose,
    AUDVIS_partymode_gizmogroup,
]
