import atexit
import threading
import time
import weakref
import numpy as np

from ..recording import AudVisRecorder

_threads = weakref.WeakSet()
_atexit_registered = False


def shutdown_all():
    # Close every PortAudio stream from the main thread while PortAudio is still alive.
    for t in list(_threads):
        t.shutdown()


def register_atexit():
    # atexit runs LIFO, so registering after sounddevice is imported makes this run before
    # sounddevice's own exit handler terminates PortAudio.
    global _atexit_registered
    if not _atexit_registered:
        atexit.register(shutdown_all)
        _atexit_registered = True


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stream_lock = threading.Lock()
        _threads.add(self)

    def _close_stream(self):
        stream = self.stream
        self.stream = None
        if stream is None:
            return
        try:
            stream.abort()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass

    def shutdown(self, timeout=1.0):
        with self._stream_lock:
            self.kill_me = True
            self._close_stream()
        if self.is_alive() and threading.current_thread() is not self:
            self.join(timeout)

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
        self._close_stream()
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
            with self._stream_lock:
                # Re-check under the lock: shutdown() may have closed everything meanwhile.
                if self.kill_me:
                    break
                try:
                    self._restart_if_needed()
                except Exception as e:
                    self.error = str(e)
            time.sleep(.2)
        # Don't touch PortAudio here: during interpreter shutdown it may already be
        # terminated/unloaded. Streams are closed by shutdown() from the main thread.

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
