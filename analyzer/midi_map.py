"""MIDI mapping math: turns what a knob / fader / pad sends into the value of a mapped property.

No bpy here - the mappings are plain objects with the fields of AudvisMidiMapProperties, so this
is tested without Blender. Built for standard (absolute) controllers: CC knobs and faders send
0..127, pads and keys send notes (velocity) or CC buttons (127 / 0).
"""

PRESS = .5  # a CC button counts as pressed from 64 up


def lookup(snapshot, kind, number, channel=0, device_key=None):
    """(value 0..1 or None if never received, held, presses) of one control.
    snapshot = (notes, controls, note-on counts) of MidiRealtimeAnalyzer.snapshot(); channel 0 = any."""
    if snapshot is None:
        return None, False, 0
    notes, controls, counts = snapshot
    value, presses = None, 0
    for device, channels in list((controls if kind == 'cc' else notes).items()):
        if device_key is not None and device != device_key:
            continue
        for ch, values in list(channels.items()):
            if channel and ch != channel:
                continue
            if number in values:
                value = max(value or 0.0, values[number] / 127)
    if kind == 'note':
        for device, channels in list(counts.items()):
            if device_key is not None and device != device_key:
                continue
            for ch, values in list(channels.items()):
                if not channel or ch == channel:
                    presses += values.get(number, 0)
        held = value is not None and value > 0
        return (value if held else 0.0), held, presses
    return value, value is not None and value >= PRESS, presses


class MapState:
    """Runtime state of one mapping (not saved)."""

    def __init__(self):
        self.presses = None  # note-on count / CC button presses seen so far
        self.held = False
        self.raw = None  # last knob value 0..1
        self.toggled = False
        self.target = None  # where the knob wants the value
        self.value = None  # smoothed value (before rounding to the property type)
        self.written = None  # what the property got - set by the caller after writing
        self.picked_up = False

    def press_events(self, kind, held, presses):
        """How many new presses since the last tick."""
        if kind == 'note':
            new = 0 if self.presses is None else max(0, presses - self.presses)
            self.presses = presses
        else:  # CC button: rising edge
            new = 1 if held and not self.held and self.presses is not None else 0
            self.presses = 0
        self.held = held
        return new


def shape(x, m):
    """0..1 knob -> property value: invert, curve, Min..Max."""
    x = 0.0 if x < 0 else 1.0 if x > 1 else x
    if m.invert:
        x = 1 - x
    if m.curve != 1:
        x = x ** m.curve
    return m.range_min + (m.range_max - m.range_min) * x


def step(m, state, raw, held, presses, current):
    """New value for the property, or None to leave it alone.
    current = the property's value now (to detect outside changes for Pickup)."""
    first = state.presses is None
    new_presses = state.press_events(m.kind, held, presses)
    if first and m.response in ('toggle', 'momentary'):  # take over the current state, don't flip it
        if current is not None:
            state.toggled = abs(current - shape(1.0, m)) < abs(current - shape(0.0, m))
        state.raw = 1.0 if held else 0.0
        return None
    if m.response == 'toggle':
        if new_presses % 2:
            state.toggled = not state.toggled
            return shape(1.0 if state.toggled else 0.0, m)
        return None
    if m.response == 'momentary':
        if state.raw is None or held != (state.raw > 0):
            state.raw = 1.0 if held else 0.0
            return shape(state.raw, m)
        return None
    # fader / knob (notes: velocity while held)
    if raw is None:
        return None
    moved = raw != state.raw
    state.raw = raw
    if not moved and (not m.smoothing or state.value is None or state.value == state.target):
        return None
    target = shape(raw, m)
    if m.pickup:
        if state.written is not None and current is not None and abs(current - state.written) > 1e-6:
            state.picked_up = False  # changed elsewhere (mouse, keyframes): pick it up again
        if not state.picked_up:
            span = abs(m.range_max - m.range_min) or 1.0
            last = state.target
            crossed = last is not None and current is not None and (last - current) * (target - current) <= 0
            state.target = target
            if current is None or abs(target - current) <= .03 * span or (moved and crossed):
                state.picked_up = True
                state.value = None  # start smoothing from the picked-up point
            else:
                return None
    state.target = target
    if m.smoothing and state.value is not None:
        value = state.value + (target - state.value) * (1 - m.smoothing)
        if abs(value - target) < 1e-4 * (abs(m.range_max - m.range_min) or 1.0):
            value = target
    else:
        value = target
    state.value = value
    return value


def presses(m, state, held, presses_count):
    """New press events of a mapping that triggers an action."""
    return state.press_events(m.kind, held, presses_count)
