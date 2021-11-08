def generators_ui_sequence(self, context, props):
    col = self.layout.column(align=True)
    col.prop(props, "channel")
    if context.scene.sequence_editor:
        col.prop_search(props, "sound_sequence", context.scene.sequence_editor, "sequences_all",
                        icon='SOUND')
        if props.sound_sequence in context.scene.sequence_editor.sequences_all:
            sequence = context.scene.sequence_editor.sequences_all[props.sound_sequence]
            if sequence.type != 'SOUND':
                row = col.row()
                row.alert = True
                row.label(text="Selected Sequence is not a sound")


def generators_ui_midi(self, context, midi_props):
    box = self.layout.box().column(align=True)
    box.label(text="MIDI")
    box.prop_search(midi_props, "device",
                    context.scene.audvis.midi_realtime, "inputs",
                    text="Device",
                    icon='PLAY_SOUND')
    box.prop_search(midi_props, "file",
                    context.scene.audvis.midi_file, "midi_files",
                    text="File")
    if midi_props.file in context.scene.audvis.midi_file.midi_files:
        midifile = context.scene.audvis.midi_file.midi_files[midi_props.file]

        box.prop_search(midi_props, "track",
                        midifile, "tracks",
                        text="Track")
    else:
        box.prop(midi_props, "track", text="Track")
    box.prop(midi_props, "channel", text="Channel")