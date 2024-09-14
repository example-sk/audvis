import bpy

for g in bpy.data.grease_pencils:
    bpy.data.grease_pencils.remove(g)

bpy.ops.object.gpencil_add(radius=1, view_align=False, location=(0, 0, 0), rotation=(0, 0, 0), type='EMPTY')
gpencil = bpy.context.object.data
gpencil.layers.new("")
layer = gpencil.layers.new("")
frame = layer.frames.new(1)
strokes = [frame.strokes.new() for i in range(15)]

r = 50
max_values = 70

i = [-1]


def callback(driver):
    i[0] += 1
    v = i[0] % max_values
    for j in range(len(strokes)):
        stroke = strokes[j]
        val = driver(j * r, (j + 1) * r) * 3
        if len(stroke.points) < max_values:
            stroke.points.add(1, pressure=.1, strength=1)
        p = stroke.points[v]
        p.co[0] = v / 10 - 3.2
        p.co[2] = j / 4 + val / 100 - 1.7


bpy.audvis.register_script("test", callback)
