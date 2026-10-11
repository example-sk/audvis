"""Regression checks for API adapters without requiring Blender."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

with patch.dict(sys.modules, {"bpy": NS()}):
    spec = importlib.util.spec_from_file_location("audvis_utils_test", Path(__file__).resolve().parents[1] / "utils.py")
    utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(utils)


class BlenderCompatibilityTests(unittest.TestCase):
    def test_modern_curve_uses_requested_property(self):
        action = NS(fcurve_ensure_for_datablock=Mock())
        owner = object()
        utils.action_add_fcurve(action, owner, '["midi_note"]', -1)
        action.fcurve_ensure_for_datablock.assert_called_once_with(owner, data_path='["midi_note"]', index=0)

    def test_modern_curve_preserves_array_index(self):
        action = NS(fcurve_ensure_for_datablock=Mock())
        owner = object()
        utils.action_add_fcurve(action, owner, "scale", 2)
        action.fcurve_ensure_for_datablock.assert_called_once_with(owner, data_path="scale", index=2)

    def test_remove_adjacent_curves_in_each_channelbag(self):
        keep = NS(data_path="keep")
        curves = [NS(data_path="midi_a"), NS(data_path="midi_b"), keep]
        action = NS(layers=[NS(strips=[NS(channelbags=[NS(fcurves=curves)])])])
        utils.action_remove_fcurves(action, "midi_")
        self.assertEqual(utils.action_get_fcurves(action), [keep])

    def test_legacy_action_cleanup(self):
        curves = [NS(data_path="midi_a"), NS(data_path="midi_b")]
        utils.action_remove_fcurves(NS(fcurves=curves), "midi_")
        self.assertEqual(curves, [])

    def test_sequencer_adapts_and_handles_missing_editor(self):
        self.assertEqual(utils.get_all_vse_strips(NS(sequence_editor=None)), ())
        for modern in [False, True]:
            editor = NS(**({"strips": [1], "strips_all": [1, 2]} if modern else
                           {"sequences": [1], "sequences_all": [1, 2]}))
            self.assertEqual(utils.get_vse_strips(editor), [1])
            self.assertEqual(utils.get_all_vse_strips(NS(sequence_editor=editor)), [1, 2])
