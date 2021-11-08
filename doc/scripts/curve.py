"""
press ALT+P to run this script
"""

import math

import bpy

import audvis

POINTS_COUNT = 30
WIDTH = 5

xxx = WIDTH / POINTS_COUNT

curve = None
if "BezierCurve" in bpy.context.scene.objects:
    curve = bpy.context.scene.objects["BezierCurve"].data
else:
    bpy.ops.curve.primitive_bezier_curve_add()
    curve = bpy.context.object.data
    bpy.context.object.rotation_euler[0] = math.pi / 2
curve.dimensions = '2D'
curve.bevel_depth = .1

curve.splines.remove(curve.splines[0])

spline = curve.splines.new('BEZIER')
spline.use_cyclic_u = True
spline.bezier_points.add(POINTS_COUNT + 1)


def callback(driver):
    spline = curve.splines[0]
    loc = (0, 0, 0)

    point = spline.bezier_points[0]
    point.co = (0, 0, 0)
    point.handle_left = point.co
    point.handle_right = point.co

    point = spline.bezier_points[-1]
    point.co = (WIDTH + xxx, 0, 0)
    point.handle_right = point.co
    point.handle_left = point.co

    for i in range(1, len(spline.bezier_points) - 1):
        val = driver(i * 30, (i + 1) * 30) * .1
        point = spline.bezier_points[i]
        loc = (i / POINTS_COUNT * WIDTH, val, 0)
        point.co = loc
        point.handle_right = (loc[0] + xxx, loc[1], loc[2])
        point.handle_left = (loc[0] - xxx, loc[1], loc[2])


audvis.register_script("test", callback)
