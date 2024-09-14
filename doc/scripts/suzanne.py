import bpy
import math

freq_range = 10

if 'Suzanne' in bpy.data.objects:
    obj = bpy.data.objects['Suzanne']
    bpy.data.objects.remove(obj)
bpy.ops.mesh.primitive_monkey_add(size=3.5)
obj = bpy.context.object
obj.rotation_euler[2] = .5
mesh = obj.data
orig = []
normals = []
for v in mesh.vertices:
    orig.append(v.co.to_tuple())
    n = v.co.copy()
    n.normalize()
    normals.append(n)


def callback(driver):
    for i in range(len(mesh.vertices)):
        frm = i * freq_range
        to = frm + freq_range
        val = math.log(driver(frm, to) * .3 + 1) / 4
        o = orig[i]
        n = normals[i]
        mesh.vertices[i].co = (
            o[0] + (n[0]) * val,
            o[1] + (n[1]) * val,
            o[2] + (n[2]) * val,
        )


bpy.audvis.register_script("test", callback)
