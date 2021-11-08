import bpy

NAME = "video to curve"
LAYER_NAME = "video"


def run(scene, conts):
    if scene.audvis.video_contour_object is None:
        curve = bpy.data.curves.new(name=NAME, type="CURVE")
        obj = bpy.data.objects.new(name=NAME, object_data=curve)
        scene.audvis.video_contour_object = obj
        bpy.context.collection.objects.link(obj)
    else:
        obj = scene.audvis.video_contour_object
        curve = obj.data

    for spline in curve.splines:
        curve.splines.remove(spline)
    for contour in conts:
        spline = curve.splines.new(type="NURBS")
        spline.points.add(len(contour)-1)
        for index in range(len(contour)):
            spline.points[index].co[:3] = contour[index]
            spline.points[index].co[3] = 1
    obj.update_tag()
