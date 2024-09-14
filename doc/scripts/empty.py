"""
press ALT+P to run this script
"""

import math
import bpy

def callback(driver):
    print(driver(10, 100))


bpy.audvis.register_script("test", callback)
