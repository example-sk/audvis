import bpy
import math
import audvis
import random

for g in bpy.data.grease_pencils:
    bpy.data.grease_pencils.remove(g)

bpy.ops.object.gpencil_add(radius=1, location=(0, 0, 0), rotation=(0, 0, 0), type='EMPTY')
gpencil = bpy.context.object.data
gpencil.layers.new("")
layer = gpencil.layers.new("")
frame = layer.frames.new(1)
strokes = [frame.strokes.new() for i in range(15)]
[stroke.points.add(1) for stroke in strokes]
r = 10
max_values = 150


def callback(driver):
    for j in range(len(strokes)):
        stroke = strokes[j]
        val = driver(j * r, (j + 1) * r) * 10
        stroke.points.add(1, pressure=10, strength=val*100)
        # stroke.points.add(1, pressure=val, strength=1)
        p = stroke.points[-1]
        p_old = stroke.points[-2]
        p.co = p_old.co
        p.co[0] = p_old.co[0] + math.sin(val) * .03
        i = random.randint(1,2)
        p.co[i] = p_old.co[i] + math.cos(val) * .03
        while len(stroke.points)>max_values:
            stroke.points.pop(index=0)


audvis.register_script("test", callback)

