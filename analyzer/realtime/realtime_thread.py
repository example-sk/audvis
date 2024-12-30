import threading
import time
import numpy as np

from ..recording import AudVisRecorder


class RealtimeThread(threading.Thread):
    requested_name = None
    requested_channels = 1
    current_name = None
    current_channels = 1
    stream = None
    samplerate = None
    kill_me = False
    callback_data = None
    sd = None
    error = None
    force_reload = False
    recorder = None  # type: AudVisRecorder

    def _restart_if_needed(self):
        req = self.requested_name
        req_channels = self.requested_channels
        cur = self.current_name
        cur_channels = self.current_channels
        if not self.force_reload and req == cur and req_channels == cur_channels:
            return
        self.force_reload = False
        self.current_name = req
        self.current_channels = self.requested_channels
        self.callback_data = None
        if self.stream and not self.stream.stopped:
            self.stream.stop()
        if req is None:
            if self.callback_data is not None:
                self.callback_data = None
            return
        kwargs = {
            'dtype': 'float32',
            'channels': req_channels,
            'callback': self._stream_cb,
            'blocksize': 256,  # TODO: select
            'device': None,
        }
        i = 0
        for device in self.sd.query_devices():
            if device['name'] == req:
                kwargs['device'] = i
                break
            i += 1
        if req != '_auto_' and kwargs['device'] is None:
            return
        self.stream = self.sd.InputStream(**kwargs)
        self.stream.start()
        self.samplerate = self.stream.samplerate

    def run(self):
        self.last_chunks = []
        while self._thread_continue():
            try:
                self._restart_if_needed()
            except Exception as e:
                self.error = str(e)
            time.sleep(.2)
        if self.stream and not self.stream.stopped:
            self.stream.stop()

    def _thread_continue(self):
        if self.kill_me:
            return False
        if not threading.main_thread().is_alive():
            return False
        if not threading.current_thread().is_alive():
            return False
        return True

    def _stream_cb(self, indata, frames, time, status):
        try:
            self.recorder.write(indata, int(self.samplerate), self.stream.channels)

            self.last_chunks.append(np.copy(indata))
            if len(self.last_chunks) > 1000:
                self.last_chunks = self.last_chunks[-1000:]
            self.error = None
            if self.callback_data is None:
                self.callback_data = indata
            else:
                if len(indata[0]) != len(self.callback_data[0]):
                    self.callback_data = indata
                else:
                    self.callback_data = np.concatenate((self.callback_data[-1048576:], indata))
        except Exception as e:
            print('audvis realtime recorder', e)
