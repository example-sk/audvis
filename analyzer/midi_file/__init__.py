import re

from ...utils import midi_note_to_number
from ..analyzer import Analyzer

regexp = re.compile('ch([0-9]+)_n([0-9]+)')


class MidiFileAnalyzer(Analyzer):
    _thread = None
    _last_data = None

    def load(self):
        pass

    def _parse_midifile(self, midifile, scene):
        # custom attributes for sequence can't be animated, at least until 2.93 alpha
        result = []
        midifile.fix_fps()
        fps = scene.render.fps / scene.render.fps_base
        endframe = sum([
            midifile.time_length * fps,
            midifile.frame_start,
            - midifile.animation_offset_start,
            - midifile.animation_offset_end
        ])
        if midifile.frame_start > scene.frame_current_final or endframe < scene.frame_current_final:
            return result
        request_frame = sum([scene.frame_current_final,
                             -midifile.frame_start,
                             midifile.animation_offset_start,
                             ])
        for track in midifile.tracks:
            if not track.enable:
                continue
            common_path = track.path_from_id()
            for fcurve in scene.animation_data.action.fcurves:
                if fcurve.data_path.startswith(common_path):
                    tmp = fcurve.data_path.replace(common_path, '').replace('["', '').replace('"]', '')
                    regexp_result = regexp.match(tmp)
                    if regexp_result:
                        channel = regexp_result.group(1)
                        note = regexp_result.group(2)
                        result.append((
                            midifile.name,
                            track.name,
                            int(channel),
                            int(note),
                            fcurve.evaluate(request_frame)
                        ))
        return result

    def on_pre_frame(self, scene, frame):
        if not scene.audvis.midi_file.enable:
            return
        if not scene.animation_data or \
                not scene.animation_data.action \
                or len(scene.audvis.midi_file.midi_files) == 0:
            self._last_data = None
            return
        new_data = []
        for midifile in scene.audvis.midi_file.midi_files:
            if midifile.enable:
                new_data += self._parse_midifile(midifile, scene)
        self._last_data = new_data

    def driver(self, low=None, high=None, ch=None, **kwargs):
        midi_note = kwargs.get("midi", None)
        if (type(midi_note) is list or type(midi_note) is tuple) and len(midi_note) in [2, 3]:
            midi_note = kwargs.get("midi", None)
            if (type(midi_note) is list or type(midi_note) is tuple) and len(midi_note) in [2, 3]:
                return self._midi_multi_note_driver(low=None, high=None, ch=None, **kwargs)
            else:
                midi_note = midi_note_to_number(midi_note)
        track = kwargs.get("track", None)
        file = kwargs.get("file", None)
        if self._last_data is None:
            return 0
        if midi_note is None or midi_note >= 127 or midi_note < 0:
            return 0
        if self._last_data is None:
            return 0
        for item in self._last_data:
            if item[3] == 0:
                continue
            if file is not None and file != '' and item[0] != file:
                continue
            if track is not None and track != '' and item[1] != track:
                continue
            if ch is not None and ch != "all" and 1 <= int(ch) <= 16 and int(ch) != item[2]:
                continue
            if midi_note is not None and item[3] != midi_note:
                continue
            if item[4] != 0.0:
                return item[4]
        return 0
