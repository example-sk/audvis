import copy
import os.path
from typing import List, Tuple, Dict, Literal
import aud
import numpy as np

import bpy


def _get_tmp_fcurve(data_path="tmp"):
    action_name = "AudvisDawHelperAction"
    if action_name in bpy.data.actions:
        action = bpy.data.actions[action_name]
    else:
        action = bpy.data.actions.new(action_name)
    for fcurve in action.fcurves:
        if fcurve.data_path == data_path:
            fcurve.keyframe_points.clear()
            return fcurve
    return action.fcurves.new(data_path)


class Audio:
    raw_data: List
    warps: List[Tuple[float, float]]
    loop_start: float
    loop_end: float
    time: float
    duration: float
    play_start: float

    def __init__(self, raw_data, warps: List[Tuple[float, float]],
                 loop_start: float, loop_end: float,
                 time: float, duration: float, play_start: float):
        self.raw_data = raw_data
        self.warps = warps
        self.loop_start = loop_start
        self.loop_end = loop_end
        self.time = time
        self.duration = duration
        self.play_start = play_start

    def to_points(self, interval: float, clip, samplerate) -> List[Tuple[float, float]]:
        loop_duration = self.loop_end - self.loop_start
        result = []
        time_map_fcurve = _get_tmp_fcurve()
        time_map_fcurve.keyframe_points.add(len(self.warps))
        for i in range(len(self.warps)):
            time_map_fcurve.keyframe_points[i].interpolation = 'LINEAR'
            time_map_fcurve.keyframe_points[i].co = self.warps[i]
        fcurve_x_cursor: float = self.play_start
        beats_x_cursor: float = 0.0
        duration = min(self.duration, clip.duration)
        while beats_x_cursor < duration:
            seconds_of_sound: float = time_map_fcurve.evaluate(fcurve_x_cursor)
            index = int(seconds_of_sound * samplerate)
            if index >= len(self.raw_data):
                index = len(self.raw_data) - 1
            y_value = self.raw_data[index]
            result.append((beats_x_cursor, y_value))
            beats_x_cursor += interval
            fcurve_x_cursor += interval
            if fcurve_x_cursor > self.loop_end:
                fcurve_x_cursor -= loop_duration
        return result


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


def _trim_notes(notes: List[Note], start: float, end: float, add: float = 0.0):
    res = []
    for note in notes:
        if start <= note.time < end:
            note = copy.copy(note)
            if note.time + note.duration > end:
                note.duration = end - note.time
            note.time = note.time - start + add
            res.append(note)
    return res


class Clip:
    time: float
    duration: float
    name: str | None
    color: Tuple[float, float, float, float] | None
    notes: List[Note]
    audio: List[Audio]

    def __init__(self, time: float, duration: float, name: str, color: Tuple[float, float, float, float]):
        self.name = name
        self.color = color
        self.time = time
        self.duration = duration
        self.notes = []
        self.audio = []

    def get_notes_range(self) -> None | Tuple[float, float]:
        res: List | None = None
        for note in self.notes:
            if res is None:
                res = [note.key, note.key]
            else:
                if note.key < res[0]:
                    res[0] = note.key
                if note.key > res[1]:
                    res[1] = note.key
        if res is None:
            return 0.0, 0.0
        return res[0], res[1]

    def consolidate_notes(self,
                          play_start: float = 0.0,
                          loop: bool = False,
                          loop_start: float | None = None,
                          loop_end: float | None = None):
        new_list: List[Note] = []
        start = 0.0
        if play_start != 0.0:
            start = play_start
        elif loop_start is not None:
            start = loop_start
        end = self.duration
        if loop:
            end = loop_end
        new_list += _trim_notes(self.notes, start, end)
        if loop:
            time_cursor: float = end - start
            while time_cursor < self.duration:
                new_list += _trim_notes(self.notes, loop_start, loop_end, time_cursor)
                time_cursor += loop_end - loop_start
        new_new_list = []
        for note in new_list:
            if note.time < self.duration:
                new_new_list.append(note)
                if note.time + note.duration > self.duration:
                    note.duration = self.duration - note.time
        self.notes = new_new_list


class Track:
    name: str
    color: tuple
    clips: List[Clip]

    def __init__(self, name: str, color: Tuple[float, float, float, float]):
        self.name = name
        self.color = color
        self.clips = []


InterpolationType = Literal["constant", "linear"]


class TempoEvent:
    tempo: float
    interpolation: InterpolationType
    time: float | None

    def __init__(self, tempo: float, interpolation: Literal["constant", "linear"], time: float | None = None,
                 bezier_controls: Tuple[Tuple[float, float], Tuple[float, float]] | None = None):
        self.tempo = tempo
        self.interpolation = interpolation
        self.time = time
        self.bezier_controls = bezier_controls

    def __repr__(self):
        return "\ntime: {}, tempo: {}, interpolation: {}".format(self.time, self.tempo, self.interpolation)


class Arrangement:
    name: str | None
    tracks: List[Track]
    basic_bpm: float
    tempo_changes: List[TempoEvent]
    duration: float
    audio_map: Dict[str, object]

    def __init__(self, name: str | None = None):
        self.name = name
        self.tracks = []
        self.bpm = 110
        self.tempo_changes = []
        self.duration = 0.0
        self.audio_map = {}

    def load_audio(self, filepath: str, identifier: str, samplerate: int):
        if not os.path.exists(filepath):
            print("File not found: ", filepath)
            return
        sound = aud.Sound(filepath)
        sound = sound.rechannel(1)
        sound = sound.resample(samplerate, False)
        data = sound.data()
        data = np.reshape(data, len(data))
        self.audio_map[identifier] = data

    def is_audio_loaded(self, identifier: str):
        return identifier in self.audio_map

    def calc_duration(self):
        max_time = 0.0
        for track in self.tracks:
            for clip in track.clips:
                max_time = max(max_time, clip.time + clip.duration)
        self.duration = max_time

    def calc_tempo_to_time(self) -> List[Tuple[float, float]]:
        if len(self.tempo_changes) == 0:
            return [
                (0, 0),
                (self.duration * (60 / self.basic_bpm), self.duration)
            ]
        fcurve = _get_tmp_fcurve("tmp")
        fcurve.keyframe_points.add(len(self.tempo_changes))
        for i in range(len(self.tempo_changes)):
            point = fcurve.keyframe_points[i]
            tc = self.tempo_changes[i]
            point.co = (tc.time, tc.tempo)
            point.handle_left_type = 'FREE'
            point.handle_right_type = 'FREE'
            point.handle_left = point.co  # TODO: support for bezier curves in tempo (.als files)
            point.handle_right = point.co  # TODO: support for bezier curves in tempo (.als files)
        x = 0.0
        calculated_time = 0.0
        step = .0001
        x_max = fcurve.keyframe_points[-1].co[0]
        x_max = max(x_max, self.duration)
        last_value = fcurve.evaluate(x)
        result = []
        next_keyframe = -1
        while x <= x_max:
            if next_keyframe < calculated_time:
                result.append((calculated_time, x))
                next_keyframe = calculated_time + .02  # in seconds
            x += step
            current_value = fcurve.evaluate(x)
            calculated_time += step * (60 / min(last_value, current_value))
            last_value = current_value
        result.append((calculated_time, x))
        return result

    def fix_zero_length_notes(self, default_duration: float, threshold: float):
        if default_duration <= threshold:
            return
        for track in self.tracks:
            for clip in track.clips:
                for note in clip.notes:
                    if note.duration <= threshold:
                        note.duration = default_duration

    def print(self):
        print('ARRANGEMENT duration: {} basic_bpm: {}'.format(self.duration, self.basic_bpm))
        for t in self.tracks:
            print(' TRACK: {}'.format(t.name))
            for clip in t.clips:
                print('  CLIP: {}, time: {}, duration: {}'.format(clip.name, clip.time, clip.duration))
                for note in clip.notes:
                    print('    NOTE: {}, time: {}, duration: {}'.format(note.key, note.time, note.duration))
