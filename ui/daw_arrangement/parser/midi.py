from typing import List

from ..arrangement import (Arrangement, Track, Clip, Note, TempoEvent)
from ...props.daw_arrangement import AudvisDawArrangement


def parse(filename, props):
    try:
        import mido
    except:
        return

    class MidiParser:
        def __init__(self, filename: str, props: AudvisDawArrangement):
            midi = mido.MidiFile(filename)
            self.ticks_per_beat = midi.ticks_per_beat
            self.arrangement = Arrangement()
            midi_track: mido.MidiTrack
            for midi_track in midi.tracks:
                track = Track(name=midi_track.name, color=(1, 1, 1, 1))
                self.parse_tempo(midi_track)
                (notes, duration) = self.parse_notes(midi_track)
                if len(notes):
                    clip = Clip(time=0.0, color=(1, 1, 1, 1), duration=duration, name="")
                    clip.notes = notes
                    track.clips.append(clip)
                    self.arrangement.tracks.append(track)
                    self.arrangement.duration = max(self.arrangement.duration, clip.duration)
            for track in self.arrangement.tracks:
                track.clips[0].duration = self.arrangement.duration
            self.arrangement.print()

        def parse_tempo(self, midi_track):
            result = []
            time = 0.0
            time_signature = (4, 4)
            for msg in midi_track:
                time += msg.time
                if msg.type == 'time_signature':
                    time_signature = (msg.numerator, msg.denominator)
                if msg.type == 'set_tempo':
                    if len(result) > 0:
                        result.append(
                            TempoEvent(tempo=result[-1].tempo, interpolation="constant",
                                       time=time / self.ticks_per_beat)
                        )
                    result.append(TempoEvent(
                        tempo=mido.tempo2bpm(msg.tempo, time_signature),
                        interpolation="constant",
                        time=time / self.ticks_per_beat
                    ))
            if len(result) > 0:
                self.arrangement.basic_bpm = result[0].tempo
            if len(result) > 1:
                self.arrangement.tempo_changes = result

        def parse_notes(self, midi_track):
            started_notes = {}
            time = 0.0
            result = []
            max_time = 0.0
            for msg in midi_track:
                time += msg.time
                if msg.type == 'note_on':
                    note = Note(time=time / self.ticks_per_beat, velocity=msg.velocity, ch=1, duration=0, key=msg.note,
                                rel=0.0)
                    started_notes[msg.note] = note
                    result.append(note)
                elif msg.type == 'note_off':
                    if msg.note in started_notes:
                        started_notes[msg.note].duration = time / self.ticks_per_beat - started_notes[msg.note].time
                        del started_notes[msg.note]
                        max_time = time / self.ticks_per_beat
            return (result, max_time)

    return MidiParser(filename, props).arrangement
