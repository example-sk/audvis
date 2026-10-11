"""Run with python3 -m unittest discover -s tests."""
import copy
import importlib
import pathlib
import sys
import types
import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Import the geometry code without running the add-on's bpy registration.
PACKAGE = '_audvis_gp_test'
for suffix, directory in [('', ROOT), ('.analyzer', ROOT / 'analyzer'),
                          ('.analyzer.shapemodifier', ROOT / 'analyzer/shapemodifier')]:
    module = types.ModuleType(PACKAGE + suffix)
    module.__path__ = [str(directory)]
    sys.modules[module.__name__] = module
compat = importlib.import_module(PACKAGE + '.grease_pencil_compat')
modifier = importlib.import_module(PACKAGE + '.analyzer.shapemodifier.greasepencil')


class LegacyPoints(list):
    def foreach_get(self, name, target):
        values = [getattr(p, name) for p in self]
        target[:] = [v for co in values for v in co] if name == 'co' else values

    def foreach_set(self, name, values):
        for i, point in enumerate(self):
            setattr(point, name, values[i * 3:i * 3 + 3] if name == 'co' else values[i])


class CompatibilityTests(unittest.TestCase):
    def test_object_detection(self):
        for kind in ('GPENCIL', 'GREASEPENCIL'):
            self.assertTrue(compat.is_grease_pencil(NS(type=kind)))
        self.assertFalse(compat.is_grease_pencil(NS(type='MESH')))
        self.assertFalse(compat.is_grease_pencil(None))

    def test_data_collection_across_versions(self):
        self.assertEqual(compat.data_collection(NS(grease_pencils='legacy')), 'legacy')
        self.assertEqual(compat.data_collection(NS(grease_pencils='annotations', grease_pencils_v3='new')), 'new')
        self.assertEqual(compat.data_collection(NS(grease_pencils='new')), 'new')

    def test_remove_and_move_signatures(self):
        for modern in (False, True):
            with self.subTest(modern=modern):
                frame = NS(frame_number=5)
                if modern:
                    frame.drawing = NS()
                layer = NS(frames=Mock())
                compat.remove_frame(layer, frame)
                layer.frames.remove.assert_called_once_with(5 if modern else frame)
                compat.move_frame(layer, frame, 0)
                if modern:
                    layer.frames.move.assert_called_once_with(5, 0)
                else:
                    self.assertEqual(frame.frame_number, 0)

    def test_copy_replaces_target_without_instancing(self):
        class Frames(list):
            remove = Mock()
            copy = Mock()
        source = NS(frame_number=0, drawing=NS())
        target = NS(frame_number=1, drawing=NS())
        frames = Frames([source, target])
        compat.copy_drawing_frame(NS(frames=frames), source, 1)
        frames.remove.assert_called_once_with(1)
        frames.copy.assert_called_once_with(0, 1, instance_drawing=False)

    def test_empty_contours_do_not_call_add_strokes(self):
        drawing = NS(add_strokes=Mock())
        compat.add_contours(NS(drawing=drawing), [[], []])
        drawing.add_strokes.assert_not_called()

    def test_modern_contours_are_visible(self):
        points = [NS(), NS()]
        drawing = NS(add_strokes=Mock(), strokes=[NS(points=points)], tag_positions_changed=Mock())
        contour = [(0, 0, 0), (1, 2, 3)]
        compat.add_contours(NS(drawing=drawing), [[], contour])
        drawing.add_strokes.assert_called_once_with([2])
        self.assertEqual(points[1].position, contour[1])
        self.assertGreater(points[0].radius, 0)
        self.assertEqual(points[0].opacity, 1)
        drawing.tag_positions_changed.assert_called_once()

    def test_deformation_preserves_source_and_maps_properties(self):
        for modern in (False, True):
            for mode, field in [('location-z', 'position' if modern else 'co'),
                                ('pressure', 'radius' if modern else 'pressure'),
                                ('strength', 'opacity' if modern else 'strength')]:
                with self.subTest(modern=modern, mode=mode):
                    point = NS(position=[1, 2, 3], radius=.25, opacity=.5) if modern else NS(co=[1, 2, 3], pressure=.25, strength=.5)
                    points = [point] if modern else LegacyPoints([point])
                    source = NS(points=points, material_index=2, line_width=10)
                    target = copy.deepcopy(source)
                    settings = NS(animtype=mode, operation='add', vector=None, freq_step_calc=1,
                                  freq_seq_type='midi', midi=NS(offset=0, channel=0, track='', file='', device=''),
                                  add=0, factor=1)
                    obj = NS(audvis=NS(shapemodifier=settings))
                    original = copy.deepcopy(getattr(point, field))
                    modifier._stroke(obj, source, target, lambda **kw: .1, [0], [1], modern=modern)
                    result = getattr(target.points[0], field)
                    self.assertAlmostEqual(result[2] if isinstance(result, list) else result,
                                           (original[2] if isinstance(original, list) else original) + .1)
                    self.assertEqual(getattr(point, field), original)
                    self.assertEqual(target.material_index, 2)

    def test_baking_zero_does_not_modify_source(self):
        settings = NS(gpencil_layer_changed=False, is_baking=True)
        obj = NS(audvis=NS(shapemodifier=settings))
        modifier.modify_greasepencil(obj, NS(frame_current=0), None)


if __name__ == '__main__':
    unittest.main()
