"""
press ALT+P to run this script
"""

import bpy
import bpy
import math

import audvis

object = bpy.data.objects['Cube']

def deps_part_system():
    degp = bpy.context.evaluated_depsgraph_get()
    return object.evaluated_get(degp).particle_systems[0]


def callback(driver):
    particle_system = deps_part_system()
    particles = particle_system.particles

    scene = bpy.context.scene
    curframe = scene.frame_current_final
    fps = scene.render.fps / scene.render.fps_base

    # at start-frame, clear the particle cache
    if curframe == scene.frame_start:
        object.particle_systems[0].seed += 0

    i = 0
    cnt = 0
    for part in particles:
        i += 1

        part.birth_time = bpy.context.scene.frame_start
        part.die_time = bpy.context.scene.frame_end
        if part.location[2] < -1:
            part.location[2] = 2
        if part.alive_state == 'ALIVE':
            cnt += 1
            j = (i * 3) % 2000
            dist = math.log(driver(j, j + 10) + 1) * .5 + 1
            # dist = (driver(j, j + 10) * .1) + 1
            z = i / 10 - curframe / fps / 5 + driver(j, j+20) * .3
            print("z", z, math.cosh(1 - z * .01))
            part.location = (
                    math.cos(i - curframe / fps) * dist * max(0, 1-abs(z)*.02),
                    math.sin(i - curframe / fps) * dist * max(0, 1-abs(z)*.02),
                    z % 4 - 2,
            )
            part.velocity = (0, 0, 0)
        elif part.alive_state == 'UNBORN':
            pass
        else:
            print(part.alive_state, part.die_time)

    print(cnt)



audvis.register_script("test", callback)
