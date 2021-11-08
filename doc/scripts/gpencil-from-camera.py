"""
press ALT+P to run this script
"""

import bpy
import cv2

import audvis

OBJECT_NAME = "video to gpencil"
if OBJECT_NAME in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects[OBJECT_NAME])
bpy.ops.object.add(type='GPENCIL')
obj = bpy.context.object
obj.name = OBJECT_NAME
layer = obj.data.layers.new(name="")


def callback(driver):
    while len(layer.frames):
        layer.frames.remove(layer.frames[0])
    frame = layer.frames.new(1)
    img = cv2.imread(bpy.context.scene.audvis.video_image.filepath)
    imgGry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    chain_approx = cv2.CHAIN_APPROX_NONE
    chain_approx = cv2.CHAIN_APPROX_SIMPLE
    chain_approx = cv2.CHAIN_APPROX_TC89_KCOS
    # chain_approx = cv2.CHAIN_APPROX_TC89_L1
    ret, thrash = cv2.threshold(imgGry, 100 , 150, chain_approx)
    contours , hierarchy = cv2.findContours(thrash, cv2.RETR_TREE, chain_approx)
    bbb = 0
    d = 100 - driver(10, 500)*500
    d = max(10, d)
    d = 15
    for contour in contours:
        contour = cv2.approxPolyDP(contour, 0.002 * cv2.arcLength(contour, True), True)
        if len(contour) < d:
            continue
        stroke = frame.strokes.new()
        bbb += 1
        stroke.line_width = driver(bbb*100, bbb*100+100) * 150 + .01
        stroke.points.add(len(contour))
        size = max(len(img), len(img[0]))
        size = 1/size
        for aaa in range(len(contour)):
            bbb += 1
            stroke.points[aaa].co = (
                -contour[aaa][0][0] * size + .5,
                -contour[aaa][0][1] * size + .5,
                0
            )

callback(audvis.audvis.driver)


audvis.register_script("test", callback)
