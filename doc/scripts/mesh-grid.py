import bpy

mesh = bpy.data.objects['Grid'].data
freq_range = 10


def callback(driver):
    for i in range(0, len(mesh.vertices)):
        frm = i * freq_range
        to = frm + freq_range
        val = driver(frm, to) / 15
        mesh.vertices[i].co[2] = val


bpy.audvis.register_script("test", callback)
