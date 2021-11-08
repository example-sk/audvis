import bpy

NAME = "video to mesh"


def run(scene, conts):
    if scene.audvis.video_contour_object is None:
        mesh = bpy.data.meshes.new(name=NAME)
        obj = bpy.data.objects.new(name=NAME, object_data=mesh)
        scene.audvis.video_contour_object = obj
        bpy.context.collection.objects.link(obj)
    else:
        obj = scene.audvis.video_contour_object
        mesh = obj.data
    if obj.mode != 'OBJECT':
        return

    mesh.clear_geometry()
    for contour in conts:
        old_verts_count = len(mesh.vertices)
        mesh.vertices.add(len(contour))
        for index in range(len(contour)):
            mesh.vertices[old_verts_count + index].co = contour[index]
        old_edges_count = len(mesh.edges)
        if len(contour) >= 2:
            mesh.edges.add(len(contour) - 1)
            for index in range(1, len(contour) - 1):
                edge = mesh.edges[old_edges_count + index]
                edge.vertices = [old_verts_count + index - 1, old_verts_count + index]
    obj.update_tag()