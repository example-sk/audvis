import threading
import time

import bpy

from . import realtime_thread

from ..analyzer import Analyzer
from ..recording import AudVisRecorder


class RealtimeAnalyzer(Analyzer):
    status = 'init'
    supported = None
    stream = None
    current_stream_name = None
    sd = None
    thread = None
    recorder = AudVisRecorder()
    device_name = None
    last_chunks = []

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
            t = realtime_thread.RealtimeThread(daemon=True)
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
