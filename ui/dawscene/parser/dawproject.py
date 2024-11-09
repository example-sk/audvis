import zipfile
from xml.etree import ElementTree

from ..scene import (Scene, Track, Clip, Note, TempoEvent)


def parse(filepath) -> Scene:
    zip = zipfile.ZipFile(file=filepath, mode='r')
    xml = ElementTree.parse(zip.open('project.xml'))
    return DawProjectParser(xml).scene


class DawProjectParser:
    xml: ElementTree
    scene: Scene
    track_by_id: dict
    line_height = .3

    def __init__(self, xml):
        self.track_by_id = {}
        self.xml = xml
        self.scene = Scene()
        self.all_tracks = {}
        self.read_tempo()
        self.read_tracks()
        self.read_lines()
        self.scene.calc_duration()
        # self.scene.print()

    def read_tempo(self):
        tempo_el = self.xml.find('./Transport/Tempo')
        self.scene.basic_bpm = float(tempo_el.attrib['value'])
        for tempo_point_el in self.xml.findall('./Arrangement/TempoAutomation/RealPoint'):
            self.scene.tempo_changes.append(TempoEvent(
                float(tempo_point_el.attrib['value']),
                tempo_point_el.attrib['interpolation'],
                float(tempo_point_el.attrib['time'])
            ))

    def read_tracks(self):
        for track_el in self.xml.findall('./Structure//Track'):
            color = _parse_color(track_el.attrib['color']) if 'color' in track_el.attrib else None
            track = Track(name=track_el.attrib['name'], color=color)
            self.track_by_id[track_el.attrib['id']] = track
            self.scene.tracks.append(track)

    def read_lines(self):
        lanes = self.xml.findall('./Arrangement/Lanes/Lanes')
        for lane in lanes:
            track = self.track_by_id[lane.attrib['track']]
            for clip_el in lane.findall('./Clips/Clip'):
                self.parse_clip(track, clip_el)

    def parse_clip(self, track: Track, clip_el):
        color = (.1, .5, .1, 1)
        if "color" in clip_el.attrib:
            color = _parse_color(clip_el.attrib['color'])
        elif track and track.color:
            color = track.color
        clip = Clip(
            name=clip_el.attrib['name'] if 'name' in clip_el.attrib else None,
            time=float(clip_el.attrib['time']),
            duration=float(clip_el.attrib['duration']),
            color=color)
        playStart = float(clip_el.attrib['playStart'])
        self._add_notes_in_timerange(clip, clip_el.findall('./Notes/Note'),
                                     time_start=playStart, time_end=playStart + clip.duration,
                                     add_time=-playStart)
        if "loopStart" in clip_el.attrib:
            loop_start = float(clip_el.attrib['loopStart'])
            loop_end = float(clip_el.attrib['loopEnd'])
            loop_duration = loop_end - loop_start
            time_cursor = playStart
            while time_cursor < clip.duration:
                if time_cursor + loop_duration > clip.duration:
                    loop_end = clip.duration - time_cursor
                self._add_notes_in_timerange(clip, clip_el.findall('./Notes/Note'),
                                             time_start=loop_start, time_end=loop_end,
                                             add_time=time_cursor - playStart)
                time_cursor += loop_duration
        track.clips.append(clip)

    def _add_notes_in_timerange(self, clip: Clip, note_elements,
                                time_start: float, time_end: float,
                                add_time: float = 0.0):
        for note_el in note_elements:
            note_time = float(note_el.attrib['time'])
            note_duration = float(note_el.attrib['duration'])
            if note_duration + note_time > time_end:
                note_duration = time_end - note_time
            if time_start <= note_time < time_end:
                clip.notes.append(Note(
                    key=int(note_el.attrib['key']),
                    duration=float(note_duration),
                    velocity=float(note_el.attrib['vel']),
                    rel=float(note_el.attrib['rel']),
                    ch=int(note_el.attrib['channel']),
                    time=note_time + add_time
                ))


def _parse_color(input: str):
    tmp = input.lstrip('#')
    return (
        int(tmp[0:2], 16) / 255,
        int(tmp[2:4], 16) / 255,
        int(tmp[4:6], 16) / 255,
        1,
    )
