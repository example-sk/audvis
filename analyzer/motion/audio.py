"""Audio sampling shared by the Motion FX effects.

Every effect asks for one value per element (cascade copy, orbiting satellite...).
Values can be spread across elements by frequency band or by time delay, routed
to the left / right stereo channel, and either follow the sound (smoothed with
attack / release) or fire one-shot envelopes on beats (trigger mode).
"""
import math


def channel_layout(props, i, count):
    """(sound channel, index within that channel's group, group size) of element i."""
    if props.stereo == 'off' or props.source != 'sound':
        return props.channel, i, count
    if props.stereo == 'split':
        half = (count + 1) // 2
        side = 1 if i >= half else 0
        return props.channel + side, i - half * side, (count - half) if side else half
    side = i % 2
    return props.channel + side, i // 2, (count - side + 1) // 2


def _band(props, local):
    low = props.freq_start + (local * props.freq_step if props.spread == 'bands' else 0)
    return low, low + props.freq_width


EQ_EDGES = (20, 60, 150, 400, 1000, 2500, 6000, 12000, 20000)  # Hz, 8 shared EQ / macro bands


def eq_gain(band, cc_reader):
    """Gain (0..2) of an EQ band. A mapped MIDI knob overrides the slider once it has been moved."""
    if band.mapped and cc_reader is not None:
        cc = cc_reader(band.control, band.channel)
        if cc is not None:
            return cc * 2.0
    return band.gain


def eq_band(props, scene, cc_reader):
    """(low Hz, high Hz, gain) of the EQ band the sound settings opted into, or None."""
    index = getattr(props, 'eq_band', 'off')
    if index == 'off' or props.source != 'sound':
        return None
    i = int(index)
    return EQ_EDGES[i - 1], EQ_EDGES[i], eq_gain(getattr(scene.audvis, 'eq_band_%d' % i), cc_reader)


def sample(props, driver, ch, local, eq=None):
    """Raw value for one channel / band, already multiplied by props.factor (and the EQ band gain)."""
    if props.source == 'off':
        return 0.0
    if props.source == 'midi':
        note = props.midi_note + (local if props.spread == 'bands' else 0)
        val = driver(midi=note,
                     ch=props.midi.channel,
                     track=props.midi.track,
                     file=props.midi.file,
                     device=props.midi.device)
    else:
        kwargs = {}
        if props.sound_sequence != '':
            kwargs['seq'] = props.sound_sequence
        if props.sequence_channel > 0:
            kwargs['seq_channel'] = props.sequence_channel
        if eq is None:
            low, high = _band(props, local)
        else:
            low = eq[0] + (local * props.freq_step if props.spread == 'bands' else 0)
            high = low + eq[1] - eq[0]
        val = driver(low, high, ch=ch, **kwargs) * (1.0 if eq is None else eq[2])
    return val * props.factor


def envelope(shape, x):
    """One-shot trigger envelope, x = 0 at the hit .. 1 at the end."""
    if x < 0 or x >= 1:
        return 0.0
    if shape == 'pulse':
        return math.sin(math.pi * x)
    if shape == 'hold':
        return 1.0 if x < .8 else (1 - x) / .2
    return (1 - x) ** 2


def _consecutive(last_frame, frame):
    return last_frame is not None and 0 < frame - last_frame <= 1


class MotionAudio:
    def __init__(self, owner=None):
        self.owner = owner  # MotionEngine: its cc_reader drives MIDI-mapped EQ band gains
        self._states = {}  # (kind, key) -> (frame, state before frame, state after frame)
        self._history = {}  # key -> {frame: {channel: value}}

    def reset(self):
        self._states.clear()
        self._history.clear()

    def _step(self, kind, key, frame, count, advance):
        """Run advance(previous state or None) once per frame. Calling again for the same
        frame (settings changed while paused) redoes the step instead of stepping twice.
        After a jump (scrubbing) the previous state is dropped."""
        last = self._states.get((kind, key))
        if last is not None and last[0] == frame:
            before = last[1]
        elif last is not None and _consecutive(last[0], frame):
            before = last[2]
        else:
            before = None
        if before is not None and len(before[0]) != count:
            before = None
        after = advance(before)
        self._states[(kind, key)] = (frame, before, after)
        return after

    def raw_values(self, key, props, driver, count, scene, frame):
        layout = [channel_layout(props, i, count) for i in range(count)]
        eq = eq_band(props, scene, getattr(self.owner, 'cc_reader', None))
        if props.spread != 'delay':
            return [sample(props, driver, ch, local, eq) for ch, local, _ in layout]
        history = self._history.setdefault(key, {})
        current = {ch: sample(props, driver, ch, 0, eq) for ch in set(ch for ch, _, _ in layout)}
        history[frame] = current
        window = count * props.delay + 2
        if len(history) > window * 4 + 100:
            for f in [f for f in history if f < frame - window]:
                del history[f]
        out = []
        for ch, local, _ in layout:
            f = frame - local * props.delay
            if f in history:
                out.append(history[f][ch])
            elif f < scene.frame_start:
                out.append(0.0)  # before the song starts: silence
            else:
                out.append(current[ch])  # not played through yet (scrubbing)
        return out

    def values(self, key, props, driver, count, scene, frame):
        """One value per element. Follow mode: smoothed sound. Trigger mode: 0..1 envelopes."""
        raw = self.raw_values(key, props, driver, count, scene, frame)
        if props.response == 'trigger':
            return self._trigger(key, props, raw, count, frame)

        def smooth(before):
            if before is None:
                return (raw,)
            out = []
            for prev, cur in zip(before[0], raw):
                speed = props.attack if cur > prev else props.release
                out.append(prev + (cur - prev) * speed)
            return (out,)

        return self._step('smooth', key, frame, count, smooth)[0]

    def _trigger(self, key, props, raw, count, frame):
        def advance(before):
            if before is None:  # don't fire on the first frame we see - we don't know the past
                return raw, [None] * count, [0.0] * count
            last_raw, hits, _ = before
            hits = list(hits)
            for i, (prev, cur) in enumerate(zip(last_raw, raw)):
                rising = cur >= props.threshold > prev
                ready = hits[i] is None or frame - hits[i] >= props.cooldown
                if rising and ready:
                    hits[i] = frame
            out = [0.0 if h is None else envelope(props.trigger_shape, (frame - h) / max(1, props.trigger_length))
                   for h in hits]
            return raw, hits, out

        return self._step('trigger', key, frame, count, advance)[2]

    def accumulate(self, key, amount, scene, frame):
        """Running sum of amount per frame, restarting at the scene's first frame.
        Used to push orbits forward by sound without jumps."""
        last = self._states.get(('acc', key))  # (frame, sum before this frame or None, sum)
        if frame <= scene.frame_start:
            base, value = None, 0.0
        elif last is not None and last[0] == frame:
            base = last[1]
            value = last[2] if base is None else base + amount
        elif last is not None and _consecutive(last[0], frame):
            base = last[2]
            value = base + amount
        else:  # jumped: keep the position, don't add
            base, value = None, last[2] if last is not None else 0.0
        self._states[('acc', key)] = (frame, base, value)
        return value


def read_cc(cc_reader, props):
    """MIDI CC (0..1) of a live control, or None if it isn't mapped."""
    if not props.enable or cc_reader is None:
        return None
    return cc_reader(props.control, props.channel)


def apply_cc(cc_reader, props, value):
    cc = read_cc(cc_reader, props)
    if cc is None:
        return value
    if props.mode == 'replace':
        return props.range_min + (props.range_max - props.range_min) * cc
    if props.mode == 'multiply':
        return value * (props.range_min + (props.range_max - props.range_min) * cc)
    return value + props.range_min + (props.range_max - props.range_min) * cc


def apply_cc_mods(cc_reader, props, mods):
    """Let a mapped MIDI CC change one of the effect's live-control values in mods."""
    if props.target in mods:
        mods[props.target] = apply_cc(cc_reader, props, mods[props.target])
    return mods
