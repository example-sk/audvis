import gzip
from xml.etree import ElementTree

from .ableton_color_map import ableton_color_map
from ..arrangement import (Arrangement, Track, Clip, Note, TempoEvent)


def parse(filepath) -> Arrangement:
    zip = gzip.open(filename=filepath, mode='r')
    xml = ElementTree.parse(zip)
    arrangement = AbletonLiveSetParser(xml).arrangement
    return arrangement


class AbletonLiveSetParser:
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
        self.arrangement.calc_duration()
        self.arrangement.print()

    def read_tempo(self):
        tempo_el = self.xml.find('./LiveSet/MasterTrack/DeviceChain/Mixer/Tempo/Manual')
        automation_target = self.xml.find('./LiveSet/MasterTrack/DeviceChain/Mixer/Tempo/AutomationTarget').attrib['Id']
        self.arrangement.basic_bpm = float(tempo_el.attrib['Value'])
        for tempo_point_el in self.xml.findall(
                './LiveSet/MasterTrack/AutomationEnvelopes'
                '/Envelopes/AutomationEnvelope/EnvelopeTarget/PointeeId[@Value="{}"]'
                '/../../'
                '/Automation/Events/FloatEvent'.format(
                    automation_target)):
            self.arrangement.tempo_changes.append(TempoEvent(
                float(tempo_point_el.attrib['Value']),
                'bezier' if "CurveControl1Y" in tempo_point_el.attrib else 'linear',
                float(tempo_point_el.attrib['Time']),
                bezier_controls=(
                    (float(tempo_point_el.attrib['CurveControl1X']), float(tempo_point_el.attrib['CurveControl1Y'])),
                    (float(tempo_point_el.attrib['CurveControl2X']), float(tempo_point_el.attrib['CurveControl2Y'])),
                ) if "CurveControl1Y" in tempo_point_el.attrib else None
            ))

    def read_tracks(self):
        for track_el in self.xml.findall('./LiveSet/Tracks/*'):
            if track_el.tag not in ['MidiTrack', 'AudioTrack']:
                continue
            color_el = track_el.find('./Color')
            color = None
            if color_el:
                color = _parse_color(color_el.attrib['Value'])
            name = track_el.find('./Name/EffectiveName').attrib['Value']
            name2 = track_el.find('./Name/UserName').attrib['Value']
            if name2 != '':
                name = name2
            track = Track(name=name, color=color)
            self.track_by_id[track_el.attrib['Id']] = track
            self.arrangement.tracks.append(track)
            self.parse_clips(track, track_el)

    def parse_clips(self, track, track_el: ElementTree):
        clip_elements = track_el.findall('./DeviceChain/MainSequencer/ClipTimeable/ArrangerAutomation/Events/*')
        for clip_el in clip_elements:
            if clip_el.tag in ['MidiClip', 'AudioClip']:
                self.parse_clip(track, clip_el)

    def parse_clip(self, track: Track, clip_el):
        color = _parse_color(clip_el.find('./Color').attrib['Value'])
        start = float(clip_el.find('./CurrentStart').attrib['Value'])
        end = float(clip_el.find('./CurrentEnd').attrib['Value'])
        clip = Clip(
            name=clip_el.attrib['Name'] if 'Name' in clip_el.attrib else None,
            time=start,
            duration=end - start,
            color=color)
        track.clips.append(clip)
        for key_track in clip_el.findall('./Notes/KeyTracks/KeyTrack'):
            key = int(key_track.find('./MidiKey').attrib['Value'])
            for note_el in key_track.findall('./Notes/MidiNoteEvent'):
                clip.notes.append(Note(
                    key=key,
                    duration=float(note_el.attrib['Duration']),
                    velocity=float(note_el.attrib['Velocity']) / 127,
                    rel=0,  # TODO float(note_el.attrib['rel']),
                    ch=1,  # TODO int(note_el.attrib['channel']),
                    time=float(note_el.attrib['Time'])
                ))
        start_relative = float(clip_el.find('./Loop/StartRelative').attrib['Value'])
        loop_start = float(clip_el.find('./Loop/LoopStart').attrib['Value'])
        loop_end = float(clip_el.find('./Loop/LoopEnd').attrib['Value'])
        if clip_el.find('./Loop/LoopOn').attrib['Value'] == 'true':
            clip.consolidate_notes(start_relative, True, loop_start, loop_end)
        else:
            clip.consolidate_notes(start_relative, False)


def _parse_color(id: str):
    tmp = ableton_color_map[id].lstrip('#')
    return (
        int(tmp[0:2], 16) / 255,
        int(tmp[2:4], 16) / 255,
        int(tmp[4:6], 16) / 255,
        1,
    )