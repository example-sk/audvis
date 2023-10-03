import bpy

NAME = "video to gpencil"
LAYER_NAME = "video"

# TODO:
"""
bpy.ops.gpencil.trace_image({'active_object': bpy.data.objects['Empty'], 'selected_objects': [bpy.data.objects['GPencil']]}, target="SELECTED", thickness=10, use_current_frame=False)
since 2.93 or 2.92 or 2.91 (warning: parameters were changed between versions)
"""


def run(scene, conts):
    if scene.audvis.video_contour_object is None:
        gpencil = bpy.data.grease_pencils.new(name=NAME)
        gpencil.pixel_factor = 20
        obj = bpy.data.objects.new(name=NAME, object_data=gpencil)
        if hasattr(bpy.context, 'temp_override'):  # blender 3.2 and higher
            with bpy.context.temp_override(object=obj):
                bpy.ops.object.material_slot_add()
        else:  # blender 3.1 and lower
            bpy.ops.object.material_slot_add({'object': obj})
        material = bpy.data.materials.new(name=NAME)
        bpy.data.materials.create_gpencil_data(material)
        obj.material_slots[0].material = material
        scene.audvis.video_contour_object = obj
        layer = gpencil.layers.new(name=LAYER_NAME)
        bpy.context.collection.objects.link(obj)
    else:
        obj = scene.audvis.video_contour_object
        gpencil = obj.data
        layer = gpencil.layers[LAYER_NAME]
    while len(layer.frames):
        layer.frames.remove(layer.frames[0])
    frame = layer.frames.new(0)

    for contour in conts:
        stroke = frame.strokes.new()
        stroke.points.add(len(contour))
        for index in range(len(contour)):
            stroke.points[index].co = contour[index]
    obj.update_tag()
