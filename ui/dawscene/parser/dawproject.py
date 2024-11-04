import zipfile
import pathlib
from xml.etree import ElementTree
from pprint import pp

from ..scene import (Scene, Track, Clip, Note, Group)


def parse(filepath) -> Scene:
    zip = zipfile.ZipFile(file=filepath, mode='r')
    xml = ElementTree.parse(zip.open('project.xml'))
    DawProjectParser(xml)
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
        self.read_tracks()
        self.read_lines()
        self.scene.print()

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
            time=clip_el.attrib['time'],
            duration=clip_el.attrib['duration'],
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
        track.clips.append(clip)


def _parse_color(input: str):
    tmp = input.lstrip('#')
    return (
        int(tmp[0:2], 16) / 255,
        int(tmp[2:4], 16) / 255,
        int(tmp[4:6], 16) / 255,
        1,
    )
