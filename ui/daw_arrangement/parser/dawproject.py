import zipfile
from xml.etree import ElementTree

from ..arrangement import (Arrangement, Track, Clip, Note, TempoEvent)


def parse(filepath) -> Arrangement:
    zip = zipfile.ZipFile(file=filepath, mode='r')
    xml = ElementTree.parse(zip.open('project.xml'))
    return DawProjectParser(xml).arrangement


class DawProjectParser:
    xml: ElementTree
    arrangement: Arrangement
    track_by_id: dict
    line_height = .3

    def __init__(self, xml):
        self.track_by_id = {}
        self.xml = xml
        self.arrangement = Arrangement()
        self.all_tracks = {}
        self.read_tempo()
        self.read_tracks()
        self.read_lines()
        self.arrangement.calc_duration()
        # self.arrangement.print()

    def read_tempo(self):
        tempo_el = self.xml.find('./Transport/Tempo')
        self.arrangement.basic_bpm = float(tempo_el.attrib['value'])
        for tempo_point_el in self.xml.findall('./Arrangement/TempoAutomation/RealPoint'):
            self.arrangement.tempo_changes.append(TempoEvent(
                float(tempo_point_el.attrib['value']),
                tempo_point_el.attrib['interpolation'],
                float(tempo_point_el.attrib['time'])
            ))

    def read_tracks(self):
        for track_el in self.xml.findall('./Structure//Track'):
            color = _parse_color(track_el.attrib['color']) if 'color' in track_el.attrib else None
            track = Track(name=track_el.attrib['name'], color=color)
            self.track_by_id[track_el.attrib['id']] = track
            self.arrangement.tracks.append(track)

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
        for note_el in clip_el.findall('./Notes/Note'):
            clip.notes.append(Note(
                key=int(note_el.attrib['key']),
                duration=float(note_el.attrib['duration']),
                velocity=float(note_el.attrib['vel']),
                rel=float(note_el.attrib['rel']),
                ch=int(note_el.attrib['channel']),
                time=float(note_el.attrib['time'])
            ))
        play_start = float(clip_el.attrib['playStart'])
        if "loopStart" in clip_el.attrib:
            loop_start = float(clip_el.attrib['loopStart'])
            loop_end = float(clip_el.attrib['loopEnd'])
            clip.consolidate_notes(play_start, True, loop_start, loop_end)
        else:
            clip.consolidate_notes(play_start, False)
        track.clips.append(clip)


def _parse_color(input: str):
    tmp = input.lstrip('#')
    return (
        int(tmp[0:2], 16) / 255,
        int(tmp[2:4], 16) / 255,
        int(tmp[4:6], 16) / 255,
        1,
    )
