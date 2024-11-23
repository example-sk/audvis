import zipfile
import tempfile
from xml.etree.ElementTree import Element

import bpy
from xml.etree import ElementTree

from ..arrangement import (Arrangement, Track, Clip, Note, TempoEvent, Audio)
from ...props.daw_arrangement import AudvisDawArrangement


def parse(filepath, props: AudvisDawArrangement) -> Arrangement:
    return DawProjectParser(filepath, props).arrangement


class DawProjectParser:
    xml: ElementTree
    arrangement: Arrangement
    track_by_id: dict
    tempdir: tempfile.TemporaryDirectory

    def __init__(self, filepath, props: AudvisDawArrangement):
        self.props = props
        self.arrangement = Arrangement()
        self.tempdir = tempfile.TemporaryDirectory(prefix="daw_audio_", dir=bpy.app.tempdir)
        with zipfile.ZipFile(file=filepath, mode='r') as archive:
            xml = ElementTree.parse(archive.open('project.xml'))
            self.unzip_audio(archive)
        bpy.asdfasdf = self.arrangement.audio_map
        self.track_by_id = {}
        self.xml = xml
        self.all_tracks = {}
        self.read_tempo()
        self.read_tracks()
        self.read_lines()
        self.arrangement.calc_duration()
        # self.arrangement.print()

    def unzip_audio(self, archive: zipfile.ZipFile):
        for name in archive.namelist():
            if name.startswith("audio/"):
                short_name = name[6:]
                if "/" not in short_name:
                    new_path = archive.extract(name, self.tempdir.name)
                    self.arrangement.load_audio(new_path, name, self.props.audio_internal_samplerate)

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

    def parse_clip(self, track: Track, clip_el: Element):
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
        self.parse_clip_audio(clip_el, clip)
        track.clips.append(clip)

    def parse_clip_audio(self, clip_el: Element, clip: Clip):
        """
        subclip: <Clip time="0.0" duration="113.73291015625" contentTimeUnit="beats" playStart="0.0" fadeTimeUnit="beats" fadeInTime="0.0" fadeOutTime="0.0">
        warp: <Warp time="191.28378868103027" contentTime="71.081056023"/>
        """
        for subclip_el in clip_el.findall('./Clips/Clip'):
            if subclip_el is None:
                return
            warps_el = subclip_el.find('.//Warps')
            if warps_el is None:
                return
            path = warps_el.find('./Audio/File').attrib['path']
            warps = []
            for warp_el in warps_el.findall('./Warp'):
                warps.append((
                    float(warp_el.attrib['time']),
                    float(warp_el.attrib['contentTime']),
                ))
            raw_data = self.arrangement.audio_map[path]
            clip.audio.append(Audio(
                raw_data=raw_data,
                warps=warps,
                loop_start=float(clip_el.attrib['loopStart'] if "loopStart" in clip_el.attrib else 0.0),
                loop_end=float(
                    clip_el.attrib['loopEnd'] if "loopEnd" in clip_el.attrib else clip_el.attrib['duration']),
                time=float(subclip_el.attrib['time']),
                duration=float(subclip_el.attrib['duration']),
                play_start=float(subclip_el.attrib['playStart']) + float(clip_el.attrib['playStart'])
            ))


def _parse_color(input: str):
    tmp = input.lstrip('#')
    return (
        int(tmp[0:2], 16) / 255,
        int(tmp[2:4], 16) / 255,
        int(tmp[4:6], 16) / 255,
        1,
    )
