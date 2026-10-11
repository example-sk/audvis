import bpy


def try_switch_scenes(current_scene):
    if not current_scene.audvis.realtime_enable:
        return False
    if not current_scene.audvis.realtime_switchscenes:
        return False
    if current_scene.frame_current == current_scene.frame_start:
        return False
    if current_scene.frame_current != current_scene.frame_end:
        return False
    if current_scene.frame_start == current_scene.frame_end:
        return False
    if len(bpy.data.scenes) < 2:
        return False
    if not hasattr(bpy.context.window, 'scene'):  # while rendering, there is not window thankfully
        return False
    if not bpy.context.screen.is_animation_playing:
        return False
    try:
        for particle_settings in bpy.data.particles:
            particle_settings.frame_start = particle_settings.frame_start  # clear cache - really ugly way
    except Exception as e:
        # print(e)
        pass
    use_next = False
    set_this_scene = None
    for s in bpy.data.scenes:
        if use_next:
            set_this_scene = s
            break
        elif s is current_scene:
            use_next = True
    if set_this_scene is None:
        set_this_scene = bpy.data.scenes[0]
    _skip_to_start(current_scene)
    switch_window_scene(bpy.context.window, set_this_scene)
    return True


def switch_window_scene(window, scene):
    """Show `scene` in `window` from its first frame and (re)start playback."""
    _skip_to_start(scene)
    window.scene = scene
    # Scene changes are evaluated after the caller returns in newer Blender
    # versions, so restarting playback synchronously can leave it stopped (or
    # stuck bouncing between frames). Restart on the next main-loop tick.
    _restart_playback(window)


def _skip_to_start(scene):
    scene.frame_current = scene.frame_start


def _restart_playback(window):
    attempts = 0

    def restart():
        nonlocal attempts
        attempts += 1
        wm = bpy.context.window_manager
        if wm is None or window not in list(wm.windows):
            return None  # window was closed
        screen = window.screen
        try:
            with bpy.context.temp_override(window=window, screen=screen):
                # Always cancel the old playback first: its timer is still
                # bound to the previous scene. Then play explicitly instead
                # of toggling, so a stale playing-flag can't leave it paused.
                if screen.is_animation_playing:
                    bpy.ops.screen.animation_cancel(restore_frame=False)
                bpy.ops.screen.animation_play()
            return None
        except (RuntimeError, AttributeError):
            # Scene evaluation and operator context can take more than one
            # tick. Give Blender a bounded retry window, then leave it alone.
            return 0.05 if attempts < 40 else None

    bpy.app.timers.register(restart, first_interval=0.0)
