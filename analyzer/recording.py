import numpy as np
import os
import random


class AudVisRecorder:
    STATUS_RUNNING = 'running'
    STATUS_STOPPED = 'stop'
    status = STATUS_STOPPED

    data = None
    samplerate = None
    channels = None

    file = None  # type: soundfile.SoundFile
    seconds = 0

    def start(self):
        self.status = 'running'

    def write(self, data, samplerate, channels):
        if self.status == self.STATUS_RUNNING:
            if self.data is None:
                self.data = data.copy()
            else:
                self.data = np.concatenate((self.data, data))
            # self.seconds = len(self.file) / samplerate # TODO
            self.seconds = len(self.data) / samplerate  # wrong, just testing
            self.samplerate = samplerate
            self.channels = channels

    def save_data(self, folder, format):
        import soundfile
        rnd = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz") for i in range(6))
        path = os.path.join(folder, "AudVisRecord-{}.{}".format(rnd, format.lower()))
        file = soundfile.SoundFile(path, mode='w', samplerate=self.samplerate, channels=self.channels, format=format)
        data = self.data
        self.data = None
        file.write(data)
        file.close()
        return path

    def stop(self):
        self.status = self.STATUS_STOPPED
