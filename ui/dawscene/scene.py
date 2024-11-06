from enum import Enum
from typing import List, Union
import numpy


class Note:
    note: int
    time: float
    duration: float
    velocity: float
    rel: float  # relative velocity

    def __init__(self, key: int, ch: int, time: float, duration: float, velocity: float, rel: float):
        self.key = key
        self.ch = ch
        self.time = time
        self.duration = duration
        self.velocity = velocity
        self.rel = rel


class Clip:
    # sound: ? TODO
    time: float
    duration: float
    name: str | None
    color: tuple | None
    notes: List[Note]

    def __init__(self, time: float, duration: float, name: str, color: tuple):
        self.name = name
        self.color = color
        self.time = time
        self.duration = duration
        self.notes = []


class Track:
    name: str
    color: tuple
    clips: List[Clip]

    def __init__(self, name: str, color: tuple):
        self.name = name
        self.color = color
        self.clips = []


class InterpolationType(Enum):
    linear: 'linear'
    constant: 'constant'


class TempoEvent:
    tempo: float
    interpolation: InterpolationType
    time: float | None
    time_seconds: float | None

    def __init__(self, tempo: float, interpolation: InterpolationType, time: float | None = None):
        self.tempo = tempo
        self.interpolation = interpolation
        self.time = time

    def __repr__(self):
        return "\ntime: {}, tempo: {}, interpolation: {}".format(self.time, self.tempo, self.interpolation)


class Scene:
    name: str | None
    tracks: List[Track]
    basic_bpm: float
    tempo_changes: List[TempoEvent]
    duration: float

    def __init__(self, name: str | None = None):
        self.name = name
        self.tracks = []
        self.bpm = 110
        self.tempo_changes = []
        self.duration: 0.0

    def calc_duration(self):
        max_time = 0.0
        for track in self.tracks:
            for clip in track.clips:
                max_time = max(max_time, clip.time + clip.duration)
        self.duration = max_time

    def calc_tempo_to_time(self) -> List[tuple]:
        """returns array of pairs (time, beats)
        Beats can be used to calculate position"""
        if len(self.tempo_changes) == 0:
            return [(0, 0), (self.duration, self.duration / self.basic_bpm)]
        res = []
        last_timestamp = 0.0
        last_tempo = 100
        calculated_time_sum = 0.0
        for tc in self.tempo_changes:
            time_diff = tc.time - last_timestamp
            avg_tempo = (last_tempo + tc.tempo) / 2
            calculated_time = (60 / avg_tempo) * time_diff
            calculated_time_sum += calculated_time
            res.append((
                calculated_time_sum,
                tc.time,
            ))
            last_tempo = tc.tempo
            last_timestamp = tc.time
        if last_timestamp < self.duration:
            res.append((
                (60 / last_tempo) * (self.duration - last_timestamp),
                self.duration,
            ))
        return res

    def print(self):
        print('SCENE duration: {}'.format(self.duration))
        for t in self.tracks:
            print(' TRACK: {}'.format(t.name))
            for clip in t.clips:
                print('  CLIP: {}, time: {}, duration: {}'.format(clip.name, clip.time, clip.duration))
                for note in clip.notes:
                    print('    NOTE: {}, time: {}, duration: {}'.format(note.key, note.time, note.duration))
