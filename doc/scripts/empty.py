"""
press ALT+P to run this script
"""

import math
import bpy

import audvis

def callback(driver):
    print(driver(10, 100))


audvis.register_script("test", callback)
