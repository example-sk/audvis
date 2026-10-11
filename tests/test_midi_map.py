"""python3 -m unittest tests.test_midi_map - MIDI mapping math, no Blender needed."""
import importlib.util
import pathlib
import unittest
from types import SimpleNamespace as NS

spec = importlib.util.spec_from_file_location(
    "midi_map", pathlib.Path(__file__).resolve().parents[1] / "analyzer" / "midi_map.py")
midi_map = importlib.util.module_from_spec(spec)
spec.loader.exec_module(midi_map)


def mapping(**kw):
    m = dict(kind='cc', response='range', range_min=0.0, range_max=10.0, invert=False, curve=1.0,
             smoothing=0.0, pickup=False)
    m.update(kw)
    return NS(**m)


def snap(controls=None, notes=None, counts=None):
    return notes or {}, controls or {}, counts or {}


class Lookup(unittest.TestCase):
    def test_cc_channel_device(self):
        s = snap(controls={'Dev': {1: {7: 127.0}}, 'Other': {2: {7: 0.0}}})
        self.assertEqual(midi_map.lookup(s, 'cc', 7)[0], 1.0)
        self.assertEqual(midi_map.lookup(s, 'cc', 7, channel=2)[0], 0.0)
        self.assertEqual(midi_map.lookup(s, 'cc', 7, device_key='Other')[0], 0.0)
        self.assertIsNone(midi_map.lookup(s, 'cc', 8)[0], "never received")

    def test_note_held_and_presses(self):
        s = snap(notes={'Dev': {1: {36: 100.0}}}, counts={'Dev': {1: {36: 3}}})
        value, held, presses = midi_map.lookup(s, 'note', 36)
        self.assertAlmostEqual(value, 100 / 127)
        self.assertTrue(held)
        self.assertEqual(presses, 3)
        self.assertEqual(midi_map.lookup(s, 'note', 37), (0.0, False, 0))


class Fader(unittest.TestCase):
    def test_follow_shape(self):
        m, st = mapping(), midi_map.MapState()
        self.assertEqual(midi_map.step(m, st, .5, True, 0, 0.0), 5.0)
        self.assertIsNone(midi_map.step(m, st, .5, True, 0, 5.0), "unchanged knob doesn't write")
        m.invert = True
        st = midi_map.MapState()
        self.assertEqual(midi_map.step(m, st, .25, False, 0, 0.0), 7.5)
        m.invert, m.curve = False, 2.0
        st = midi_map.MapState()
        self.assertEqual(midi_map.step(m, st, .5, True, 0, 0.0), 2.5)

    def test_pickup(self):
        m, st = mapping(pickup=True), midi_map.MapState()
        self.assertIsNone(midi_map.step(m, st, .2, False, 0, 8.0), "far from the value: wait")
        self.assertIsNone(midi_map.step(m, st, .5, True, 0, 8.0))
        value = midi_map.step(m, st, .81, True, 0, 8.0)  # crossed 8.0 on the way up
        self.assertAlmostEqual(value, 8.1)
        st.written = value
        self.assertAlmostEqual(midi_map.step(m, st, .3, False, 0, value), 3.0, msg="picked up: follows")
        st.written = 3.0
        self.assertIsNone(midi_map.step(m, st, .4, False, 0, 9.0), "moved with the mouse: pick up again")

    def test_smoothing_glides(self):
        m, st = mapping(smoothing=.5), midi_map.MapState()
        self.assertEqual(midi_map.step(m, st, 0.0, False, 0, 0.0), 0.0)
        self.assertEqual(midi_map.step(m, st, 1.0, True, 0, 0.0), 5.0)
        self.assertEqual(midi_map.step(m, st, 1.0, True, 0, 5.0), 7.5, "keeps gliding with the knob still")
        for _ in range(40):
            last = midi_map.step(m, st, 1.0, True, 0, 0.0) or last
        self.assertEqual(last, 10.0)


class Buttons(unittest.TestCase):
    def test_toggle_note(self):
        m, st = mapping(kind='note', response='toggle', range_max=1.0), midi_map.MapState()
        self.assertIsNone(midi_map.step(m, st, 0.0, False, 0, 1.0), "first read takes over the state")
        self.assertEqual(midi_map.step(m, st, .8, True, 1, 1.0), 0.0, "on -> off")
        self.assertIsNone(midi_map.step(m, st, 0.0, False, 1, 0.0))
        self.assertEqual(midi_map.step(m, st, .8, True, 2, 0.0), 1.0)
        self.assertIsNone(midi_map.step(m, st, 0.0, False, 4, 1.0), "double tap between reads: no change")

    def test_hold(self):
        m, st = mapping(kind='note', response='momentary'), midi_map.MapState()
        self.assertIsNone(midi_map.step(m, st, 0.0, False, 0, 0.0))
        self.assertEqual(midi_map.step(m, st, .5, True, 1, 0.0), 10.0)
        self.assertIsNone(midi_map.step(m, st, .5, True, 1, 10.0))
        self.assertEqual(midi_map.step(m, st, 0.0, False, 1, 10.0), 0.0)

    def test_cc_button_rising_edge(self):
        m, st = mapping(response='toggle', range_max=1.0), midi_map.MapState()
        self.assertIsNone(midi_map.step(m, st, 1.0, True, 0, 0.0), "first read")
        self.assertIsNone(midi_map.step(m, st, 0.0, False, 0, 0.0))
        self.assertEqual(midi_map.step(m, st, 1.0, True, 0, 0.0), 1.0)
        self.assertIsNone(midi_map.step(m, st, 1.0, True, 0, 1.0), "held: no repeat")

    def test_action_presses(self):
        m, st = mapping(kind='note'), midi_map.MapState()
        self.assertEqual(midi_map.presses(m, st, False, 5), 0, "old presses don't fire")
        self.assertEqual(midi_map.presses(m, st, True, 6), 1)


if __name__ == "__main__":
    unittest.main()
