"""
press ALT+P to run this script
"""

import bpy

bpy.ops.curve.primitive_bezier_circle_add()
circle = bpy.context.object

bpy.ops.object.select_all(action='DESELECT')
mesh = bpy.data.meshes.new("testing")
obj = bpy.data.objects.new("testing", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_add(type='CURVE')
obj.modifiers[0].object = circle
bpy.ops.object.modifier_add(type='SKIN')

mesh.vertices.add(1)
mesh.skin_vertices[0].data[0].use_root = True


def callback(driver):
    obj.data.vertices.add(1)
    v_old = obj.data.vertices[-2]
    v = obj.data.vertices[-1]

    v.co = (v_old.co[0] + .003, v_old.co[1] + .00015, v_old.co[2])

    mesh.edges.add(1)
    mesh.edges[-1].vertices[0] = v_old.index
    mesh.edges[-1].vertices[1] = v.index

    skin_vert = obj.data.skin_vertices[0].data[-1]
    skin_vert.radius[0] = driver(10, 100) / 50 + .03
    skin_vert.radius[1] = driver(200, 300) / 50 + .03


bpy.audvis.register_script("test", callback)
