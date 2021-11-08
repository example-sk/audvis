"""
press ALT+P to run this script
"""

import math
import bpy

import audvis

freq_per_pixel = 6.1
size = [40, 40]  # Don't put too high numbers here. You will regret it very soon!
name = 'audvis'


def callback(driver):
    if name not in bpy.data.images:
        img = bpy.data.images.new(name=name, width=size[0], height=size[1])
    else:
        img = bpy.data.images[name]
    if list(img.size) != size:
        img.scale(size[0], size[1])
    arr = []
    for i in range(img.size[0] * img.size[1]):
        val = driver(i * freq_per_pixel, i * freq_per_pixel + freq_per_pixel * 3) * .5
        arr += [
            val,
            val,
            val,
            1
        ]
    img.pixels = arr


audvis.register_script("test", callback)
