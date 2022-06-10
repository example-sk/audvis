from . import midi_thread
from ..analyzer import Analyzer


class MidiRealtimeAnalyzer(Analyzer):
    _thread = None
    _last_data = None

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
            for item in scene.audvis.midi_realtime.inputs:
                if item.enable:
                    lst.append({
                        'custom_name': item.name,
                        'device_name': item.input_name,
                    })
            self._thread.requested_devices = lst

    def driver(self, low=None, high=None, ch=None, **kwargs):
        if self._last_data is None:
            return 0
        if "midi" in kwargs:
            if (type(kwargs['midi']) is list or type(kwargs['midi']) is tuple) and len(kwargs['midi']) == 2:
                multi_list = []
                for i in range(kwargs['midi'][0], kwargs['midi'][1]):
                    m_kwargs = kwargs.copy()
                    m_kwargs['midi'] = i
                    multi_list.append(self.driver(low, high, ch, **m_kwargs))
                return max(multi_list)
            else:
                midi_note = int(kwargs['midi'])
        else:
            return 0
        if midi_note >= 127 or midi_note < 0:
            return 0
        device_id = kwargs.get('device', None)
        device_key = None
        for key in self._last_data.keys():

            if device_key is not None and key != device_key:
                continue
            device_data = self._last_data[key]
            for key2 in device_data.keys():
                if ch is not None and ch != 'all' and key2 != ch:
                    continue
                channel_data = device_data[key2]
                for key3 in channel_data.keys():
                    if key3 == midi_note:
                        return channel_data[key3]
        return 0
