from typing import List, Self


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


class Group:
    children: List[Self]


class Scene:
    name: str | None
    tracks: List[Track]
    groups: List[Group]

    def __init__(self, name: str | None = None):
        self.name = name
        self.groups = []
        self.tracks = []

    def print(self):
        for t in self.tracks:
            print('TRACK: {}'.format(t.name))
            for clip in t.clips:
                print('  CLIP: {}, time: {}, duration: {}'.format(clip.name, clip.time, clip.duration))
                for note in clip.notes:
                    print('    NOTE: {}, time: {}, duration: {}'.format(note.key, note.time, note.duration))
