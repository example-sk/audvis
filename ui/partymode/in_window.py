import bpy

from ...utils import call_ops_override
from . import gizmo


def _hide_cursor(context, window):
    if not context.scene.audvis.party.hide_mouse:
        return

    def _tmp():
        window.cursor_set("NONE")

    bpy.app.timers.register(_tmp, first_interval=5)


def invoke(operator, context, event):
    operator.callbacks = []
    if True:
        bpy.ops.wm.window_new()
    else:
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
    window = context.window_manager.windows[-1]
    gizmo.partymode_windows.append(window)
    area = window.screen.areas[0]
    area.type = 'VIEW_3D'
    space = area.spaces[0]
    space.overlay.show_overlays = False
    space.shading.type = context.scene.audvis.party.shading
    space.shading.show_xray_wireframe = context.scene.audvis.party.show_xray
    space.region_3d.view_perspective = 'CAMERA'
    call_ops_override(bpy.ops.screen.screen_full_area, {
        'window': window,
        'screen': window.screen,
        'area': area,
    }, use_hide_panels=True)
    space.show_region_header = False
    call_ops_override(bpy.ops.wm.window_fullscreen_toggle, {'window': window})
    bpy.ops.object.select_all(action='DESELECT')
    _hide_cursor(context, window)
    if not window.screen.is_animation_playing:
        bpy.ops.screen.animation_play()
    screen = window.screen
    area = screen.areas[0]
    space = area.spaces[0]
    if hasattr(space, 'show_gizmo'):
        space.show_gizmo = True
        space.show_gizmo_navigate = False
    context.window_manager.windows.update()

    def _zoom():
        call_ops_override(bpy.ops.view3d.view_center_camera, {
            'window': window,
            'screen': screen,
            'area': area,
            'region': area.regions[0],
        })
        return None

    bpy.app.timers.register(_zoom, first_interval=1)
    return {'RUNNING_MODAL'}


def modal(operator, context, event):
    return {'FINISHED'}
