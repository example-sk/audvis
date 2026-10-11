import time
import traceback

from . import cascade, orbit, scatter
from .audio import MotionAudio, apply_cc

EFFECTS = ('cascade', 'orbit', 'scatter')


class MotionEngine:
    """Runs the Motion FX (cascade, scatter, orbit) of every object once per frame."""

    def __init__(self, driver, cc_reader=None):
        self.driver = driver
        self.cc_reader = cc_reader  # (control, channel) -> 0..1 or None
        self.audio = MotionAudio(self)
        self.layer_members = {}  # (owner name, effect) -> names of the user's objects it overrides
        self.gates = {}  # (owner name, effect) -> [value, target, seconds per full fade, last time]
        self.released = set()  # (owner name, effect) switched off by Release / Stop - Engage All brings them back
        self._cache = {}
        self._reported = set()

    def cached(self, key, signature, build):
        entry = self._cache.get(key)
        if entry is None or entry[0] != signature:
            entry = (signature, build())
            self._cache[key] = entry
        return entry[1]

    def invalidate(self, key=None):
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)

    # ------------------------------------------------------------ fading (Engage / Release)

    def fade(self, owner_name, effect, target, seconds, start=None):
        """Fade an effect's gate to target (0..1) over seconds of wall time - while playing or paused."""
        value = self.gate(owner_name, effect) if start is None else start
        if seconds <= 0:
            value = target
        self.gates[(owner_name, effect)] = [value, target, seconds, time.monotonic()]

    def gate(self, owner_name, effect):
        entry = self.gates.get((owner_name, effect))
        if entry is None:
            return 1.0
        value, target, seconds, last = entry
        now = time.monotonic()
        if value != target:
            step = (now - last) / seconds if seconds > 0 else 1.0
            value = min(target, value + step) if target > value else max(target, value - step)
        entry[0], entry[3] = value, now
        return value

    def is_fading(self):
        return any(entry[0] != entry[1] for entry in self.gates.values())

    def gate_state(self, owner_name, effect):
        """None, or (value, target) while a fade runs / after a release."""
        entry = self.gates.get((owner_name, effect))
        return None if entry is None else (entry[0], entry[1])

    def influence(self, owner, effect, settings, scene):
        """Effect Influence (or its MIDI CC) x Engage/Release fade x scene Master, 0..1."""
        value = settings.influence
        if settings.cc.enable and settings.cc.target == 'influence':
            value = apply_cc(self.cc_reader, settings.cc, value)
        value *= self.gate(owner.name, effect) * scene.audvis.motion_master
        return 0.0 if value < 0 else 1.0 if value > 1 else value

    # ------------------------------------------------------------ per frame

    def on_pre_frame(self, scene, frame):
        if not scene.audvis.motion_enable:
            return
        frame = scene.frame_current_final
        for obj in scene.objects:
            props = obj.audvis
            if props.cascade.enable:
                self._run(cascade.update, obj, scene, frame)
            if props.orbit.enable:
                self._run(orbit.update, obj, scene, frame)
            if props.scatter.enable and obj.type in ('MESH', 'GREASEPENCIL'):
                self._run(scatter.update, obj, scene, frame)
        for (owner_name, effect), entry in list(self.gates.items()):
            if entry[0] == entry[1] == 1.0:  # an Engage finished
                del self.gates[(owner_name, effect)]
            elif entry[0] == entry[1] == 0.0:  # a Release finished: switch the effect off
                del self.gates[(owner_name, effect)]
                owner = scene.objects.get(owner_name)
                if owner is not None and getattr(owner.audvis, effect).enable:
                    getattr(owner.audvis, effect).enable = False

    def _run(self, func, obj, scene, frame):
        try:
            func(self, obj, scene, frame)
        except Exception:
            key = (func.__module__, obj.name)
            if key not in self._reported:  # don't flood the console every frame
                self._reported.add(key)
                print("AudVis Motion FX failed for", obj.name)
                traceback.print_exc()
