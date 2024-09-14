import bpy
import random

freq_range = 50
curve = bpy.data.curves['BezierCircle']


def callback(driver):
    i = 0
    for spline in curve.splines:
        points = spline.bezier_points
        for point in points:
            i += 1
            frm = i * freq_range
            to = frm + freq_range
            val = driver(frm, to) / 30 + .02
            val += random.random() * .1
            point.radius = val


bpy.audvis.register_script("test", callback)
