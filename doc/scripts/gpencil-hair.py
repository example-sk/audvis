import bpy
from audvis import audvis
xcount = 10
ycount = 100

layer = bpy.data.grease_pencils[0].layers[0]
def cb(driver):
    while len(layer.frames):
        layer.frames.remove(layer.frames[0])
    frame = layer.frames.new(1)
    for j in range(ycount):
        stroke = frame.strokes.new()
        stroke.points.add(count=xcount, pressure=1, strength=1)
        for i in range(xcount):
            point = stroke.points[i]
            val = driver(i + j * xcount, i + 1 + j * xcount)
            point.pressure = val
            point.co = (i * .3, j * .1, val)

audvis.register_script('test', cb)