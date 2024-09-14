import bpy
import math

for g in bpy.data.grease_pencils:
    bpy.data.grease_pencils.remove(g)

# CONFIG
move_z = .0008
rot_z = .03
count = 1
init_length = 1000
max_length = 2000

# INIT
objects = []
i = 0

for j in range(count):
    bpy.ops.object.gpencil_add(radius=1, location=(j - count/2+.5, 0, 0), rotation=(0, 0, 0), type='EMPTY')
    objects.append(bpy.context.object)
    gpencil = bpy.context.object.data
    layer = gpencil.layers.new("")
    frame = layer.frames.new(1)
    frame.strokes.new()

# MAIN CODE
def stroke_cb(stroke_index, driver):
    global i
    
    obj = objects[stroke_index]
    stroke = obj.data.layers[0].frames[0].strokes[0]
    hz = stroke_index * 100

    stroke.points.add(1, pressure=.1, strength=1)
    p = stroke.points[-1]
    p.co[0] = math.cos(i * rot_z) * .4
    p.co[1] = math.sin(i * rot_z) * .4
    val = 0
    if driver:
        val = driver(hz, 100 + hz) + 1
    p.pressure = val + 1
    p.co[2] = val / 100 - obj.location[2]
    
    if len(stroke.points) > max_length:
        stroke.points.pop(index=0)
    
def callback(driver):
    global i
    i += 1
    
    for j in range(len(objects)):
        obj = objects[j]
        obj.location[2] = -i * move_z
        obj.rotation_euler[2] = -i * rot_z + math.pi*1.5
        stroke_cb(j, driver)
    

for j in range(init_length):
    callback(None)

bpy.audvis.register_script("test", callback)
