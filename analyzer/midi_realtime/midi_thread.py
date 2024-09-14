import collections
import os
import importlib
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


@dataclass
class _MidiControlMessage:
    control: int
    value: int
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
    data_controls = None
    samplerate = None
    kill_me = False
    callback_data = None
    error = None
    force_reload = False
    recorder = None  # type: AudVisRecorder
    python_path = None
    regexp_control = re.compile(r"^(\d{1,2}) (c|)(\d{1,3}) (\d{1,3})$")
    _kill_all = False
    last_msg = None

    def run(self):
        self.python_path = glob(os.path.join(os.path.realpath(sys.prefix), 'bin', 'python*'))[0]
        self.inputs = {}
        self.data = nested_dict()
        self.data_controls = nested_dict()
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
                match = self.regexp_control.match(line)
                if match:
                    if match.group(2) == 'c':
                        msg = _MidiControlMessage(
                            channel=int(match.group(1)),
                            control=int(match.group(3)),
                            value=int(match.group(4)),
                            time=0,
                            input_name=key,
                        )
                    else:
                        msg = _MidiNoteMessage(on=True,
                                               channel=int(match.group(1)),
                                               note=int(match.group(3)),
                                               velocity=int(match.group(4)),
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
        data_notes = deepcopy(self.data)
        data_controls = deepcopy(self.data_controls)
        for msg in msgs:
            if type(msg) == _MidiNoteMessage:
                val = msg.velocity * 1.0 if msg.on else 0.0
                data_notes[msg.input_name][msg.channel][msg.note] = val
                if val == 0.0:
                    del data_notes[msg.input_name][msg.channel][msg.note]
                    if len(data_notes[msg.input_name][msg.channel]) == 0:
                        del data_notes[msg.input_name][msg.channel]
                        if len(data_notes[msg.input_name]) == 0:
                            del data_notes[msg.input_name]
            elif type(msg) == _MidiControlMessage:
                data_controls[msg.input_name][msg.channel][msg.control] = msg.value * 1.0
        self.data = data_notes
        self.data_controls = data_controls

    def restart_all_inputs(self):
        self._kill_all = True

    def _ensure_inputs(self):
        kill_all = False
        if self._kill_all:
            self.data = nested_dict()
            self.data_controls = nested_dict()
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
        mido_spec = importlib.util.find_spec("mido")
        if not mido_spec:
            return []
        libs_path = os.path.dirname(os.path.dirname(mido_spec.origin))
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
