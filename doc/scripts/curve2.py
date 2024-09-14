"""
press ALT+P to run this script
"""

import bpy

curve = bpy.context.scene.objects["BezierCurve"].data


def clean():
    curve.splines.remove(curve.splines[0])
    curve.splines.new('BEZIER')


clean()


def callback(driver):
    if bpy.context.scene.frame_current == 1:
        clean()
    spline = curve.splines[0]
    spline.bezier_points.add(1)
    point = spline.bezier_points[-1]
    point.co = (len(spline.bezier_points) / 2, 0, 0)
    point.radius = driver(10, 100)
    point.handle_left = point.co
    point.handle_right = point.co


bpy.audvis.register_script("test", callback)
