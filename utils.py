import bpy

MidiNoteMap = {}

for octave in range(-2, 10):
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


# reason: https://developer.blender.org/docs/release_notes/4.4/python_api/#video-sequencer-strips
def get_all_vse_strips(scene):
    if scene.sequence_editor is None:
        return ()
    if hasattr(scene.sequence_editor, 'strips_all'):
        return scene.sequence_editor.strips_all
    return scene.sequence_editor.sequences_all


def get_vse_strips(editor):
    return getattr(editor, "strips" if hasattr(editor, "strips") else "sequences")


# reason: https://developer.blender.org/docs/release_notes/4.4/upgrading/slotted_actions/
def action_get_fcurves(action):
    if hasattr(action, 'fcurves'):
        return action.fcurves
    res = []
    for a in action.layers:
        for b in a.strips:
            for c in b.channelbags:
                for d in c.fcurves:
                    res.append(d)
    return res


def action_remove_fcurves(action, data_path_starts_with):
    if hasattr(action, 'fcurves'):
        for fcurve in list(action.fcurves):
            if (fcurve.data_path.startswith(data_path_starts_with)):
                action.fcurves.remove(fcurve)
        return
    for a in action.layers:
        for b in a.strips:
            for c in b.channelbags:
                for fcurve in list(c.fcurves):
                    if (fcurve.data_path.startswith(data_path_starts_with)):
                        c.fcurves.remove(fcurve)


def action_add_fcurve(action, datablock, data_path, index):
    if hasattr(action, "fcurves"):  # backcompat before Blender 5.0
        return action.fcurves.new(data_path=data_path, index=index)
    else:
        return action.fcurve_ensure_for_datablock(datablock, data_path=data_path, index=max(index, 0))
