import collections
import os
import re
import subprocess
import sys
import threading
import time
from copy import deepcopy
from dataclasses import dataclass
# https://www.midi.org/specifications-old/item/table-1-summary-of-midi-message
from glob import glob
from queue import Queue

from ...ui import install_lib

NOTE_OFF = 8  # 1000xxxx
NOTE_ON = 9  # 1001xxxx
COMMON_KEY = '_audvis_common'

nested_dict = lambda: collections.defaultdict(nested_dict)


@dataclass
class _MidiNoteMessage:
    on: bool
    note: int
    velocity: int
    time: int
    channel: int
    input_name: str


class _AsyncFileReader(threading.Thread):
    def __init__(self, fd):
        self.queue = Queue()
        assert callable(fd.readline)
        threading.Thread.__init__(self, daemon=True)
        self._fd = fd

    def run(self):
        for line in iter(self._fd.readline, ''):
            self.queue.put(line.rstrip())

    def eof(self):
        return not self.is_alive() and self.queue.empty()


class MidiThread(threading.Thread):
    requested_devices = None
    inputs = None
    data = None
    samplerate = None
    kill_me = False
    callback_data = None
    error = None
    force_reload = False
    recorder = None  # type: AudVisRecorder
    python_path = None
    regexp_note = re.compile(r"^(\d{1,2}) (\d{1,3}) (\d{1,3})$")
    _kill_all = False
    last_msg = None

    def run(self):
        self.python_path = glob(os.path.join(os.path.realpath(sys.prefix), 'bin', 'python*'))[0]
        self.inputs = {}
        self.data = nested_dict()
        self.requested_devices = []
        while self._thread_continue():
            self._ensure_inputs()
            self._receive()
            time.sleep(.001)

    def _receive(self):
        keys = self.inputs.keys()
        msgs = []
        for key in keys:
            input = self.inputs[key]
            while not input['queue'].empty():
                line = input['queue'].get()
                match = self.regexp_note.match(line)
                if match:
                    msg = _MidiNoteMessage(on=True,
                                           channel=int(match.group(1)),
                                           note=int(match.group(2)),
                                           velocity=int(match.group(3)),
                                           time=0,
                                           input_name=key,
                                           )
                    self.last_msg = msg
                    msgs.append(msg)
        if len(msgs):
            self._process_messages(msgs)

    @staticmethod
    def _sort_messages_cb(msg1):
        return msg1.time

    def _process_messages(self, msgs):
        data = deepcopy(self.data)
        for msg in msgs:
            val = msg.velocity * 1.0 if msg.on else 0.0
            data[msg.input_name][msg.channel][msg.note] = val
            if val == 0.0:
                del data[msg.input_name][msg.channel][msg.note]
                if len(data[msg.input_name][msg.channel]) == 0:
                    del data[msg.input_name][msg.channel]
                    if len(data[msg.input_name]) == 0:
                        del data[msg.input_name]
        self.data = data

    def restart_all_inputs(self):
        self._kill_all = True

    def _ensure_inputs(self):
        kill_all = False
        if self._kill_all:
            self.data = nested_dict()
            self._kill_all = False
            kill_all = True
        if self.inputs is not None:
            for device_name in list(self.inputs.keys()):
                if kill_all or not self._is_device_requested(device_name):
                    # print('audvis TERMINATING midi', device_name)
                    inp = self.inputs[device_name]
                    inp['reader'].join(0)
                    inp['process'].terminate()
                    del self.inputs[device_name]
        for input_setup in self.requested_devices:
            device_name = input_setup['device_name']
            # input_device_name = input_setup['device_name']
            if device_name in self.inputs:
                continue
            # print("audvis OPENING midi", device_name, self.inputs)
            self.inputs[device_name] = self._create_input(device_name)

    def _is_device_requested(self, device_name):
        for item in self.requested_devices:
            if item['device_name'] == device_name:
                return True
        return False

    def _create_input(self, device_name):
        libs_path = install_lib.get_libs_path_latest()
        add_params = []
        if libs_path is not None:
            add_params = [
                '--libs-path',
                libs_path,
            ]
        process = subprocess.Popen([self.python_path,
                                    os.path.join(os.path.dirname(__file__), 'midi_realtime_proxy.py'),
                                    '--input-name',
                                    device_name,
                                    ] + add_params,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True
                                   )
        reader = _AsyncFileReader(process.stdout)
        reader.start()
        return {
            'reader': reader,
            'queue': reader.queue,
            'process': process,
        }

    def _thread_continue(self):
        if self.kill_me:
            return False
        if not threading.main_thread().is_alive():
            return False
        if not threading.current_thread().is_alive():
            return False
        return True
