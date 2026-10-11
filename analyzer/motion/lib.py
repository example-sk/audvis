INDEX_KEY = "audvis_motion_index"
HELPER_KEY = "audvis_motion_helper"  # instancer carriers, hidden instance sources


def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def smoothstep(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def stagger(amount, order, strength):
    """Delay the amount for elements with a higher order (0..1), so they react
    one after another instead of all at once. Still reaches 0 and 1 for all."""
    return clamp01(amount * (1 + strength) - order * strength)


def elements(collection, exclude=None):
    """Objects of a generated / chosen collection in a stable order."""
    if collection is None:
        return []
    objs = [obj for obj in collection.objects if obj != exclude and HELPER_KEY not in obj]
    objs.sort(key=lambda o: (o.get(INDEX_KEY, 1 << 30), o.name))
    return objs


def place(obj, matrix, frame, bake):
    obj.matrix_world = matrix
    if bake:
        obj.keyframe_insert("location", frame=frame)
        if obj.rotation_mode == 'QUATERNION':
            obj.keyframe_insert("rotation_quaternion", frame=frame)
        elif obj.rotation_mode == 'AXIS_ANGLE':
            obj.keyframe_insert("rotation_axis_angle", frame=frame)
        else:
            obj.keyframe_insert("rotation_euler", frame=frame)
        obj.keyframe_insert("scale", frame=frame)


def scene_time(scene, frame):
    fps = scene.render.fps / scene.render.fps_base
    return (frame - scene.frame_start) / fps
