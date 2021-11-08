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
    _skip_to_start(set_this_scene)
    bpy.context.window.scene = set_this_scene
    # override for a bug: animation stuck switching frames 1 / 2 / 1 / 2 / 1 / 2... forever:
    bpy.ops.screen.animation_play()  # pause
    bpy.ops.screen.animation_play()  # play
    # end override
    return True


def _skip_to_start(scene):
    scene.frame_current = scene.frame_start
