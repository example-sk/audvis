"""Run in each Blender version:
blender --background --factory-startup --python-exit-code 1 --python tests/blender_grease_pencil_smoke.py
"""
import pathlib
import sys
from types import SimpleNamespace as NS

import bpy

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_grease_pencil_compat import compat, modifier

# Exercise actual RNA/drawing APIs without installing optional audio dependencies.
data = compat.data_collection(bpy.data).new('AudVis compatibility smoke test')
obj = bpy.data.objects.new('AudVis compatibility smoke test', data)
bpy.context.scene.collection.objects.link(obj)
try:
    layer = data.layers.new('Audio')
    frame = layer.frames.new(5)
    compat.add_contours(frame, [[(0, 0, 1), (1, 0, 2)], [(2, 0, 3)]])
    modern = hasattr(frame, 'drawing')
    coord = 'position' if modern else 'co'
    radius = 'radius' if modern else 'pressure'
    settings = NS(gpencil_layer='', gpencil_layer_changed=False, is_baking=False,
                  order='asc', animtype='location-z', operation='add', vector=None,
                  freq_step_calc=1, freq_seq_type='midi',
                  midi=NS(offset=0, channel=0, track='', file='', device=''), add=0, factor=1)
    proxy = NS(data=data, audvis=NS(shapemodifier=settings))
    driver = lambda **kw: .25
    for _ in range(2):
        modifier.modify_greasepencil(proxy, NS(frame_current=1), driver)
        source = next(f for f in layer.frames if f.frame_number == 0)
        target = next(f for f in layer.frames if f.frame_number == 1)
        assert abs(getattr(compat.strokes(source)[0].points[0], coord)[2] - 1) < 1e-6
        assert abs(getattr(compat.strokes(target)[0].points[0], coord)[2] - 1.25) < 1e-6
        assert [len(s.points) for s in compat.strokes(target)] == [2, 1]
    settings.animtype = 'pressure'
    settings.is_baking = True
    modifier.modify_greasepencil(proxy, NS(frame_current=10), driver)
    baked = next(f for f in layer.frames if f.frame_number == 10)
    expected = getattr(compat.strokes(source)[0].points[0], radius) + .25
    assert abs(getattr(compat.strokes(baked)[0].points[0], radius) - expected) < 1e-6
    for frame in list(layer.frames):
        if frame.frame_number > 0:
            compat.remove_frame(layer, frame)
    assert [f.frame_number for f in layer.frames] == [0]
    print('PASS: Grease Pencil creation, deformation, repeated updates, bake and cleanup', bpy.app.version_string)
finally:
    bpy.data.objects.remove(obj, do_unlink=True)
    compat.data_collection(bpy.data).remove(data)
