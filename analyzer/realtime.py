import threading
import time

import bpy
import numpy as np

from .analyzer import Analyzer
from .recording import AudVisRecorder


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
            'blocksize': 256 * 2,  # TODO: select
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


class RealtimeAnalyzer(Analyzer):
    status = 'init'
    supported = None
    stream = None
    current_stream_name = None
    sd = None
    thread = None
    recorder = AudVisRecorder()
    device_name = None

    def load(self):
        try:
            import sounddevice as sd
            self.sd = sd
            self.supported = True
        except Exception as e:
            self.supported = False
            # print("AudVis", e)
            return
        scene = bpy.context.scene
        self.on_pre_frame(scene, bpy.context.scene.frame_current_final)

    def recorder_stop(self, folder, format):
        self.recorder.stop()
        self.stop()
        path = self.recorder.save_data(folder, format)
        self.restart()
        return path

    def kill(self):
        if self.thread is not None:
            self.thread.kill_me = True

    def get_error(self):
        if self.thread is not None:
            return self.thread.error

    def stop(self):
        self.thread.requested_name = None
        self.empty()

    def restart(self):
        self._load_stream(bpy.context.scene, True)

    def on_pre_frame(self, scene, frame):
        self._load_stream(scene)
        self._read_synchronous(scene)
        if self.lastdata is not None:
            self.calculate_fft()

    def _load_stream(self, scene, force_reload=False):
        if self.thread is None:
            t = RealtimeThread(daemon=True)
            t.recorder = self.recorder
            t.sd = self.sd
            self.thread = t
            t.start()
        if force_reload:
            self.thread.force_reload = True
        if scene.audvis.realtime_enable:
            prefs = bpy.context.preferences.addons[bpy.audvis._module_name].preferences
            if False and prefs.realtime_device_use_global:
                self.thread.requested_name = prefs.realtime_device
            else:
                self.thread.requested_name = self.device_name
            self.thread.requested_channels = scene.audvis.channels
        else:
            self.thread.requested_name = None
            self.thread.requested_channels = 1

    def _read_synchronous(self, scene):
        if self.thread is None:
            self.empty()
            return

        if self.thread is None or self.thread.callback_data is None:
            self.empty()
        else:
            self.samplerate = self.thread.samplerate
            self.lastdata = self.thread.callback_data[-int(scene.audvis.sample_calc * self.samplerate):]
