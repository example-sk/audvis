import bpy

MidiNoteMap = {
    'A0': 21,
    'A#0': 22,
    'Bb0': 22,
    'B0': 23,
}
for octave in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
    for i, (note, offset) in enumerate({
                                           'C': 0,
                                           'C#': 1, 'Db': 1,
                                           'D': 2,
                                           'D#': 3, 'Eb': 3,
                                           'E': 4,
                                           'F': 5,
                                           'F#': 6, 'Gb': 6,
                                           'G': 7,
                                           'G#': 8, 'Ab': 8,
                                           'A': 9,
                                           'A#': 10, 'Bb': 10,
                                           'B': 11,
                                       }.items()):
        MidiNoteMap[note + str(octave)] = 24 + ((octave - 1) * 12) + offset
        if note == 'Ab' and octave == 9:
            break


def midi_note_to_number(value):
    if type(value) is str:
        value = value.capitalize()
        if value in MidiNoteMap:
            return MidiNoteMap[value]  # 'C4' => 60
        return int(value)  # '60' => 60
    return value  # 60 => 60


def midi_number_to_note(value):
    for (note_name, midi_number) in list(MidiNoteMap.items()):
        if value == midi_number:
            return note_name
    return None


def call_ops_override(operator, override, **kwargs):
    if hasattr(bpy.context, 'temp_override'):  # blender 3.2 and higher
        with bpy.context.temp_override(**override):
            operator(**kwargs)
    else:
        operator(override, **kwargs)
