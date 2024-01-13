import os

import bpy

from ...utils import call_ops_override

workspace_name = 'audvis-party'


def _hide_cursor(context, window):
    if not context.scene.audvis.party.hide_mouse:
        return

    def _tmp():
        window.cursor_set("NONE")

    bpy.app.timers.register(_tmp, first_interval=5)


def invoke(operator, context, event):
    operator.callbacks = []
    blend_path = os.path.join(os.path.dirname(__file__), 'audvis-party-workspace.blend')
    workspace_names = bpy.data.workspaces.keys()
    bpy.ops.workspace.append_activate(idname="audvis-party", filepath=blend_path)
    new_workspace_names = bpy.data.workspaces.keys()
    found_new_ws_names = [x for x in new_workspace_names if x not in workspace_names]
    operator._workspace = bpy.data.workspaces[found_new_ws_names[0]]
    # operator._workspace = bpy.context.workspace
    bpy.ops.wm.window_fullscreen_toggle()
    bpy.context.window_manager.windows.update()
    bpy.ops.object.select_all(action='DESELECT')
    operator.callbacks.append(lambda: _play())
    operator.callbacks.append(lambda: _fullscreen(operator))
    window = context.window
    _hide_cursor(context, window)
    operator.timer = context.window_manager.event_timer_add(.01, window=window)
    return {'RUNNING_MODAL'}


def _play(requested_state=True):
    if bpy.context.screen.is_animation_playing != requested_state:
        bpy.ops.screen.animation_play()


def _fullscreen(operator):
    workspace = operator._workspace
    override = {
        'screen': workspace.screens[0],
        'area': workspace.screens[0].areas[0]
    }
    call_ops_override(bpy.ops.screen.screen_full_area, override, use_hide_panels=True)
    space = bpy.context.space_data
    if space is None:
        print("Known bug: can't setup vie3d options in the party workspace mode")
    else:
        space.overlay.show_overlays = False
        space.shading.type = bpy.context.scene.audvis.party.shading
        space.shading.show_xray_wireframe = bpy.context.scene.audvis.party.show_xray
        space.region_3d.view_perspective = 'CAMERA'


def modal(operator, context, event):
    if event.type == 'TIMER':
        if len(operator.callbacks):
            cb = operator.callbacks.pop(0)
            cb()
        else:
            context.window_manager.event_timer_remove(operator.timer)
            return {'FINISHED'}
    else:
        return {'PASS_THROUGH'}
    return {'RUNNING_MODAL'}
