import bpy

from . import (
    video_to_gpencil,
    video_to_mesh,
    video_to_curve,
)


def run(scene, cv2):
    if not scene.audvis.video_contour_enable:
        return
    if scene.audvis.video_image is None:
        return
    vco = scene.audvis.video_contour_object
    if vco is not None and vco.type != scene.audvis.video_contour_object_type:
        scene.audvis.video_contour_object = None
        bpy.data.objects.remove(vco)
        vco = None
    if vco is not None and vco.name not in scene.objects and vco.users == 1:
        scene.audvis.video_contour_object = None
        bpy.data.objects.remove(vco)
        vco = None
    conts = _contours(cv2, scene)
    if scene.audvis.video_contour_object_type == 'GPENCIL':
        video_to_gpencil.run(scene, conts)
    elif scene.audvis.video_contour_object_type == 'MESH':
        video_to_mesh.run(scene, conts)
    elif scene.audvis.video_contour_object_type == 'CURVE':
        video_to_curve.run(scene, conts)


def _contours(cv2, scene):
    props = scene.audvis
    img = cv2.imread(scene.audvis.video_image.filepath)
    if img is None:
        raise AssertionError("AudVis Contours: Image load error, because it's empty")
    imgGry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    chain_approx = getattr(cv2, props.video_contour_chain_approx)
    ret, thrash = cv2.threshold(imgGry, props.video_contour_threshold, 255, chain_approx)
    contours, hierarchy = cv2.findContours(thrash, cv2.RETR_TREE, chain_approx)
    result = []
    img_size = (len(img[0]), len(img))
    size = max(img_size[0], img_size[1])
    size = (1 / size) * props.video_contour_size
    move_by = (
        img_size[0] * size / 2,
        img_size[1] * size / 2,
    )
    for contour in contours:
        contour = cv2.approxPolyDP(contour,
                                   (props.video_contour_simplify / 1000) * cv2.arcLength(contour, True),
                                   True)
        if len(contour) >= props.video_contour_min_points_per_stroke:
            result.append([(
                c[0][0] * size - move_by[0],
                move_by[1] - c[0][1] * size,
                0) for c in contour])

    return result
