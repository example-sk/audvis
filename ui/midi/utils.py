def get_selected_midi_file(context):
    props = context.scene.audvis.midi_file
    if 0 <= props.list_index < len(props.midi_files):
        midifile = props.midi_files[props.list_index]
        if midifile.deleted:
            return None
        return midifile
    return None


def get_selected_midi_track(context):
    props = context.scene.audvis.midi_file
    midifile = get_selected_midi_file(context)
    if midifile is None:
        return None
    if 0 <= midifile.list_index < len(midifile.tracks):
        track = midifile.tracks[midifile.list_index]
        if track.deleted:
            return None
        return track
    return None