import os.path
import aud

from ..arrangement import (Arrangement, Track, Clip, Note, TempoEvent, Audio)
from ...props.daw_arrangement import AudvisDawArrangement


def parse(filepath, props) -> Arrangement:
    return AudioFileParser(filepath, props).arrangement


class AudioFileParser:
    arrangement: Arrangement

    def __init__(self, filepath, props: AudvisDawArrangement):
        if not os.path.exists(filepath):
            return
        self.arrangement = Arrangement()
        self.arrangement.basic_bpm = 110  # dummy value
        self.arrangement.load_audio(filepath, "tmp", props.audio_internal_samplerate)
        sound = aud.Sound(filepath)
        duration = sound.length / sound.specs[0]
        duration = duration / 60 * self.arrangement.basic_bpm
        track = Track(name=os.path.basename(filepath), color=(1, 1, 1, 1))
        clip = Clip(time=0, duration=duration, name="", color=(1, 1, 1, 1,))
        clip.audio.append(
            Audio(time=0, duration=clip.duration,
                  play_start=0, loop_start=0, loop_end=clip.duration,
                  warps=[(0, 0), (clip.duration, sound.length / sound.specs[0])],
                  raw_data=self.arrangement.audio_map["tmp"]))
        track.clips.append(clip)
        self.arrangement.tracks.append(track)
        self.arrangement.calc_duration()
