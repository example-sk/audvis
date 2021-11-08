import bpy

import audvis

for g in bpy.data.grease_pencils:
    bpy.data.grease_pencils.remove(g)

bpy.ops.object.gpencil_add(radius=1, view_align=False, location=(0, 0, 0), rotation=(0, 0, 0), type='EMPTY')
obj = bpy.context.object
obj.grease_pencil_modifiers.new("", type="GP_THICK").thickness = 50
gpencil = obj.data
gpencil.layers.new("")
layer = gpencil.layers.new("")
frame = layer.frames.new(1)
strokes = [frame.strokes.new() for i in range(15)]

r = +50
max_values = 70 * 3

j = -1
for stroke in strokes:
    j += 1
    for a in range(max_values):
        stroke.points.add(1, pressure=1, strength=1)
        p = stroke.points[-1]
        p.co[0] = a / 30 - 3.2
        p.co[2] = j / 4 - 1.7

i = [-1]


def callback(driver):
    i[0] += 1
    v = i[0] % max_values
    for j in range(len(strokes)):
        stroke = strokes[j]
        val = driver(j * r, (j + 1) * r) * 3
        p = stroke.points[v]
        p.co[2] = j / 4 + val / 100 - 1.7


audvis.register_script("test", callback)
