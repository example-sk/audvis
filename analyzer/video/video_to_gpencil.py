import bpy

from ...grease_pencil_compat import data_collection, remove_frame, add_contours

NAME = "video to gpencil"
LAYER_NAME = "video"

def run(scene, conts):
    if scene.audvis.video_contour_object is None:
        gpencil = data_collection(bpy.data).new(name=NAME)
        if hasattr(gpencil, "pixel_factor"):
            gpencil.pixel_factor = 20
        obj = bpy.data.objects.new(name=NAME, object_data=gpencil)
        material = bpy.data.materials.new(name=NAME)
        bpy.data.materials.create_gpencil_data(material)
        gpencil.materials.append(material)
        scene.audvis.video_contour_object = obj
        layer = gpencil.layers.new(name=LAYER_NAME)
        bpy.context.collection.objects.link(obj)
    else:
        obj = scene.audvis.video_contour_object
        gpencil = obj.data
        layer = gpencil.layers[LAYER_NAME]
    while len(layer.frames):
        remove_frame(layer, layer.frames[0])
    frame = layer.frames.new(0)

    add_contours(frame, conts)
    gpencil.update_tag()
    obj.update_tag()
