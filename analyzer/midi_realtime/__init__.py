from ...utils import midi_note_to_number
from . import midi_thread
from .midi_thread import _MidiNoteMessage
from ..analyzer import Analyzer


class MidiRealtimeAnalyzer(Analyzer):
    _thread = None
    _last_data = None
    _last_data_controls = None

    def get_last_msg(self) -> _MidiNoteMessage:
        thread = self._thread
        if not thread:
            return None
        return thread.last_msg

    def load(self):
        self._thread = midi_thread.MidiThread(daemon=True)
        self._thread.start()

    def restart(self):
        if self._thread is not None:
            self._thread.restart_all_inputs()

    def stop(self):
        pass

    def on_pre_frame(self, scene, frame):
        if scene.audvis.midi_realtime.enable:
            lst = []
            self._last_data = self._thread.data
            self._last_data_controls = self._thread.data_controls
            for item in scene.audvis.midi_realtime.inputs:
                if item.enable:
                    lst.append({
                        'custom_name': item.name,
                        'device_name': item.input_name,
                    })
            self._thread.requested_devices = lst

    def driver(self, low=None, high=None, ch=None, **kwargs):
        if self._last_data is None and self._last_data_controls is None:
            return 0
        data = self._last_data
        if ch != 'all' and type(ch) == str and ch.isnumeric():
            ch = int(ch)
        if "midi_control" in kwargs:
            midi_note = kwargs.get('midi_control')
            data = self._last_data_controls
        elif "midi" in kwargs:
            midi_note = kwargs.get("midi", None)
            if (type(midi_note) is list or type(midi_note) is tuple) and len(midi_note) in [2, 3]:
                return self._midi_multi_note_driver(low=None, high=None, ch=None, **kwargs)
            else:
                midi_note = midi_note_to_number(kwargs['midi'])
        else:
            return 0
        if midi_note >= 127 or midi_note < 0:
            return 0
        device_id = kwargs.get('device', None)
        device_key = None
        for key in data.keys():
            if device_key is not None and key != device_key:
                continue
            device_data = data[key]
            for key2 in device_data.keys():
                if ch is not None and ch != 'all' and key2 != ch:
                    continue
                channel_data = device_data[key2]
                for key3 in channel_data.keys():
                    if key3 == midi_note and channel_data[key3]:
                        return channel_data[key3]
        return 0
