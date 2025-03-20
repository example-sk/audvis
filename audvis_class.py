import importlib
import math
import random
import time

import bpy

from .analyzer import nonstop_baking
from .analyzer.analyzer import Analyzer
from .analyzer.midi_file import MidiFileAnalyzer
from .analyzer.midi_realtime import MidiRealtimeAnalyzer
from .analyzer.realtime import RealtimeAnalyzer
from .analyzer.sequence import SequenceAnalyzer
from .analyzer.shapemodifier import ShapeModifier
from .analyzer.spectrogram import SpectrogramGenerator
from .analyzer.video import VideoAnalyzer
from .scripting import Scripting
from .switchscenes import try_switch_scenes


class AudVis:
    sequence_analyzers = {}
    realtime_analyzer = None
    realtime_multi_analyzers = {}
    midi_realtime_analyzer = None
    midi_file_analyzer = None
    video_analyzer = None
    scripting = Scripting()
    _realtime_supported = None
    _recording_supported = None
    _video_supported = None
    _midi_realtime_supported = None
    input_device_options = None
    midi_input_device_options = None
    shape_modifier = None
    spectrogram_generator = None
    _mido_initialized = False

    cProfile = None

    def get_realtime_error(self):
        if self.realtime_analyzer:
            return self.realtime_analyzer.get_error()
        return False

    def get_video_error(self):
        if self.video_analyzer:
            return self.video_analyzer.error
        return False

    def is_realtime_supported(self, force=False):
        if force or self._realtime_supported is None:
            self._realtime_supported = importlib.util.find_spec('sounddevice') is not None
        return self._realtime_supported

    def is_recording_supported(self, force=False):
        if force or self._recording_supported is None:
            self._recording_supported = importlib.util.find_spec('soundfile') is not None
        return self._recording_supported

    def is_midi_realtime_supported(self, force=False):
        if force or self._midi_realtime_supported is None:
            self._midi_realtime_supported = importlib.util.find_spec('mido') is not None
        return self._midi_realtime_supported

    def is_video_supported(self, force=False):
        if force or self._video_supported is None:
            self._video_supported = importlib.util.find_spec('cv2') is not None
        return self._video_supported

    def driver(self, low=None, high=None, ch=None, **kwargs):
        start = time.time()
        scene = bpy.context.scene

        if "midi" not in kwargs and "midi_control" not in kwargs and ch is None:
            ch = scene.audvis.default_channel_sound
        elif ("midi" in kwargs or "midi_control" in kwargs) \
                and ch is None \
                and scene.audvis.default_channel_midi != 'all':
            ch = scene.audvis.default_channel_midi
        val = 0
        seq = kwargs.get('seq')
        seq_channel = kwargs.get('seq_channel')
        additive = kwargs.get('additive', False)
        if scene.audvis.realtime_multi.enable \
                and "seq" not in kwargs \
                and "midi" not in kwargs \
                and "midi_control" not in kwargs:
            for item in list(scene.audvis.realtime_multi.list):
                device = kwargs.get('device')
                if item.enable and (
                        device is None or device == item.name) and item.uuid in self.realtime_multi_analyzers:
                    rt_analyzer = self.realtime_multi_analyzers[item.uuid]
                    val += rt_analyzer.driver(low, high, ch, additive)
        elif self.realtime_analyzer \
                and self.realtime_analyzer.supported \
                and "seq" not in kwargs \
                and "midi" not in kwargs \
                and "midi_control" not in kwargs \
                and not scene.audvis.realtime_multi.enable:
            val += self.realtime_analyzer.driver(low, high, ch, additive)

        if scene.audvis.midi_realtime.enable \
                and self.midi_realtime_analyzer \
                and (seq is None or seq == ''):
            val += self.midi_realtime_analyzer.driver(low, high, ch, **kwargs)

        if scene.audvis.midi_file.enable \
                and self.midi_file_analyzer:
            val += self.midi_file_analyzer.driver(low, high, ch, **kwargs)

        if scene.sequence_editor \
                and scene.audvis.sequence_enable \
                and "midi" not in kwargs \
                and "midi_control" not in kwargs:
            for seq in scene.sequence_editor.sequences_all:
                if seq.type != 'SOUND':
                    continue
                if not hasattr(seq, "audvis"):
                    continue
                if not seq.audvis.enable:
                    continue
                if seq.name not in self.sequence_analyzers:
                    continue
                if "seq" in kwargs and kwargs["seq"] != seq.name:
                    continue
                if "seq_channel" in kwargs and kwargs["seq_channel"] != seq.channel:
                    continue
                analyzer = self.sequence_analyzers[seq.name]
                val += analyzer.driver(low, high, ch, additive)
        if math.isnan(val):
            val = 0
        ret = (val * scene.audvis.value_factor) / 10
        if not additive:
            ret = min(scene.audvis.value_max, ret)
        ret += scene.audvis.value_add
        if scene.audvis.value_noise > 0:
            ret += random.random() * scene.audvis.value_noise
        # print(". DRIVER VALUE ", "%f" % (time.time() - start))
        return ret

    def reload(self):
        if self.realtime_analyzer is not None:
            self.realtime_analyzer.stop()
        if self.video_analyzer is not None:
            self.video_analyzer.stop()
        self.shape_modifier = None
        self.spectrogram_generator = None
        self.scripting.reset()
        self.sequence_analyzers = {}

    def profiled_update_data(self, scene, dummy=None, force=False):
        if self.cProfile is None:
            import cProfile
            self.cProfile = cProfile
        p = self.cProfile.Profile()
        p.runcall(self.update_data, scene, dummy, force=force)
        p.dump_stats(file='/tmp/profile.dump')

    last_scene_name = None
    last_scene_frame = None

    def update_data(self, scene, dummy=None, force=False):
        start = time.time()
        if not force \
                and self.last_scene_name == bpy.context.scene.name \
                and self.last_scene_frame == bpy.context.scene.frame_current_final:
            return
        self.last_scene_frame = bpy.context.scene.frame_current_final
        self.last_scene_name = bpy.context.scene.name
        scene = bpy.context.scene
        # if scene != bpy.context.scene:  # material preview panel
        #    return
        if try_switch_scenes(scene):
            return
        Analyzer.fake_highpass_settings = (scene.audvis.value_highpass_freq, scene.audvis.value_highpass_factor, True)
        if scene.audvis.value_aud.enable:
            Analyzer.aud_filters = scene.audvis.value_aud
        else:
            Analyzer.aud_filters = None
        Analyzer.normalize = scene.audvis.value_normalize
        Analyzer.channels = scene.audvis.channels
        Analyzer.normalize_clamp_to = scene.audvis.value_normalize_clamp_to
        Analyzer.fadeout_type = scene.audvis.value_fadeout_type
        Analyzer.fadeout_speed = scene.audvis.value_fadeout_speed
        Analyzer.additive_type = scene.audvis.value_additive_type
        Analyzer.is_first_frame = scene.frame_current_final == scene.frame_start
        Analyzer.additive_reset_onfirstframe = scene.audvis.value_additive_reset
        subframes = scene.audvis.subframes
        if scene.audvis.realtime_enable and not scene.audvis.realtime_multi.enable and self.realtime_analyzer is None:
            self.realtime_analyzer = RealtimeAnalyzer()
            self.realtime_analyzer.device_name = scene.audvis.realtime_device
            self.realtime_analyzer.load()
        if scene.audvis.realtime_enable and scene.audvis.realtime_multi.enable:
            self.fix_realtime_multi(scene.audvis)
        for x in range(subframes, -1, -1):
            frame = scene.frame_current_final + x / (subframes + 1)
            if self.realtime_analyzer is not None and self.realtime_analyzer.supported:
                self.realtime_analyzer.device_name = scene.audvis.realtime_device
                self.realtime_analyzer.on_pre_frame(scene, frame)
            if scene.audvis.realtime_multi.enable:
                for item in scene.audvis.realtime_multi.list:
                    if item.enable and item.uuid in self.realtime_multi_analyzers:
                        rt_analyzer = self.realtime_multi_analyzers[item.uuid]
                        rt_analyzer.device_name = item.device_name
                        rt_analyzer.on_pre_frame(scene, frame)
            if scene.audvis.sequence_enable:
                self._update_sequences(scene, frame)
            if scene.audvis.midi_realtime.enable:
                self.get_midi_realtime_analyzer(scene).on_pre_frame(scene, frame)
            if scene.audvis.midi_file.enable:
                self.get_midi_file_analyzer(scene).on_pre_frame(scene, frame)
            self.scripting.run(self)
        video_analyzer = self.get_video_analyzer(scene)
        if video_analyzer is not None and video_analyzer.supported:
            video_analyzer.on_pre_frame(scene, frame)
        self._get_shape_modifier().on_pre_frame(scene, frame)
        self._get_spectrogram_generator().on_pre_frame(scene, frame)
        nonstop_baking.bake(scene)
        # print("________ FRAME UPDATE ", "%f" % (time.time() - start))

    def fix_realtime_multi(self, props):
        enabled_uuids = []
        for item in props.realtime_multi.list:
            if item.enable:
                enabled_uuids.append(item.uuid)
                if item.uuid not in self.realtime_multi_analyzers:
                    self.realtime_multi_analyzers[item.uuid] = RealtimeAnalyzer()
                    self.realtime_multi_analyzers[item.uuid].device_name = item.device_name
                    self.realtime_multi_analyzers[item.uuid].load()
                self.realtime_multi_analyzers[item.uuid].device_name = item.device_name
        for key in list(self.realtime_multi_analyzers.keys()):
            if key not in enabled_uuids:
                analyzer = self.realtime_multi_analyzers[key]
                analyzer.stop()
                del self.realtime_multi_analyzers[key]

    def get_video_analyzer(self, scene):
        if scene.audvis.video_webcam_enable and self.video_analyzer is None:
            self.video_analyzer = VideoAnalyzer()
            self.video_analyzer.load()
        return self.video_analyzer

    def get_midi_realtime_analyzer(self, scene):
        if scene.audvis.midi_realtime.enable and self.midi_realtime_analyzer is None:
            self.midi_realtime_analyzer = MidiRealtimeAnalyzer()
            self.midi_realtime_analyzer.load()
        return self.midi_realtime_analyzer

    def get_midi_file_analyzer(self, scene):
        if scene.audvis.midi_file.enable and self.midi_file_analyzer is None:
            self.midi_file_analyzer = MidiFileAnalyzer()
            self.midi_file_analyzer.load()
        return self.midi_file_analyzer

    def _get_shape_modifier(self):
        if self.shape_modifier is None:
            self.shape_modifier = ShapeModifier()
            self.shape_modifier.load(self.driver)
        return self.shape_modifier

    def _get_spectrogram_generator(self):
        if self.spectrogram_generator is None:
            self.spectrogram_generator = SpectrogramGenerator()
            self.spectrogram_generator.load(self.driver)
        return self.spectrogram_generator

    def _update_sequences(self, scene, frame):
        if not scene.sequence_editor:
            return
        if not scene.audvis.sequence_enable:
            return
        keys = dict.fromkeys(self.sequence_analyzers.keys(), [])
        for seqname in keys:
            if not seqname in scene.sequence_editor.sequences_all:
                self.sequence_analyzers.pop(seqname)
                continue
            seq = scene.sequence_editor.sequences_all[seqname]
            if not seq.audvis.enable:
                self.sequence_analyzers.pop(seqname)
        for seq in scene.sequence_editor.sequences_all:
            if not hasattr(seq, "audvis"):
                continue
            if not seq.audvis.enable:
                continue
            if not seq.name in self.sequence_analyzers:
                self.sequence_analyzers[seq.name] = SequenceAnalyzer()
                self.sequence_analyzers[seq.name].load(seq)
            self.sequence_analyzers[seq.name].on_pre_frame(scene, frame)

    def register_script(self, name, callback):
        self.scripting.register(name, callback)
        self.update_data(bpy.context.scene)
