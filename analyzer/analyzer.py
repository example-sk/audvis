import math

import aud
import bpy
import numpy as np

import audvis


def make_fake_curve_light(self, context):
    key = 'audvis curve'
    if self.fake_curve_light is None:
        light = self.fake_curve_light = bpy.data.lights.new(name=key, type='SPOT')
        light.use_fake_user = True
        light.falloff_curve.curves[0].points[0].location = (0, 1)
        light.falloff_curve.curves[0].points[1].location = (1, 1)
        light.falloff_curve.update()


class Analyzer:
    lastdata = None
    samplerate = None
    resolution_step = 1  # resolution_step=10 means resolution 10 Hz
    last_fft = None
    additive_fft = None
    fake_highpass_settings = (1000, .3, True)
    normalize = 'no'
    normalize_clamp_to = 100.0
    fadeout_type = 'off'
    fadeout_speed = .0
    additive_type = 'off'
    is_first_frame = False
    additive_reset_onfirstframe = False
    channels = 1
    aud_filters = None
    _curve_mapping_cache = None
    _curve_mapping_cache_signature = None

    def load(self):
        raise NotImplementedError()

    def driver(self, low=None, high=None, ch=1, additive=False):
        if low is None:
            return 0
        fft = self.last_fft
        if additive and self.additive_fft is not None:
            fft = self.additive_fft
        if fft is None:
            return 0
        if len(fft) < ch:
            return 0
        if low == 'max' and high is None:
            return np.argmax(fft[ch - 1]) * self.resolution_step
        i_from = math.floor(low / self.resolution_step)
        i_to = math.ceil(high / self.resolution_step)
        lst = fft[ch - 1][i_from:i_to]
        val = self._avg(lst)
        if bpy.context.scene.audvis.value_logarithm:
            val = math.log(val + 1)
        return val

    def _avg(self, arr):
        if len(arr) == 0:
            return 0
        # return np.average(arr)  # slower
        return sum(arr) / len(arr)  # faster

    def empty(self):
        self.lastdata = None
        self.last_fft = None
        self.additive_fft = None

    def on_pre_frame(self, scene, frame):
        raise NotImplementedError()

    def _apply_aud_filters(self):
        s = aud.Sound.buffer(self.lastdata, self.samplerate)
        conf = self.aud_filters
        if conf.highpass > 0:
            s = s.highpass(conf.highpass, conf.highpass_factor)
        if conf.lowpass < self.samplerate:
            s = s.lowpass(conf.lowpass, conf.lowpass_factor)
        if conf.adsr_enable:
            s = s.ADSR(conf.adsr_attack, conf.adsr_decay, conf.adsr_sustain, conf.adsr_release)
        # if conf.env_enable:
        #     s = s.envelope(conf.env_attack, conf.env_release, conf.env_threshold, conf.env_arthreshold)
        #     print("envelope")
        if hasattr(audvis, 'custom_filter'):
            s = audvis.custom_filter(s);
        s = s.resample(self.samplerate, True)
        self.lastdata = s.data()

    def calculate_fft(self):
        if self.aud_filters is not None:
            self._apply_aud_filters()
        prev_fft = self.last_fft
        prev_additive_fft = self.additive_fft
        self.last_fft = []
        self.additive_fft = []
        if not len(self.lastdata):
            return
        available_channel_count = len(self.lastdata[0])
        channel_count = min(self.channels, available_channel_count)
        for ch in range(channel_count):
            data = self.lastdata[:, ch]
            resolution = int(self.samplerate / self.resolution_step)
            norm = None
            if self.normalize == "ortho":
                norm = "ortho"
            fft = np.abs(np.fft.rfft(data, n=resolution, norm=norm))
            if self.fake_highpass_settings[2]:
                fft = self._fake_highpass(fft)
            if self.aud_filters is not None and self.aud_filters.use_fake_curve_light:
                fft = self._curve(fft)
            if self.normalize == "max":
                max_value = max(fft)
                normalize_min_value = 1
                # if max_value > normalize_min_value and max_value != 0:
                if max_value != 0:
                    fft /= max_value
            if self.normalize == "max":
                fft *= self.normalize_clamp_to
            elif self.normalize == 'ortho':
                fft *= 100

            fft_before_fadeout = fft
            # TODO: how to use this? As a result, or something like audvis(10, 100, falloff=True) ?
            if self.fadeout_type != 'off' and (prev_fft is not None) and (0 <= ch < len(prev_fft)):
                if self.fadeout_type == 'fft':
                    # https://chromium.googlesource.com/chromium/blink/+/refs/heads/main/Source/modules/webaudio/RealtimeAnalyser.cpp#186
                    fft = prev_fft[ch] * (1 - self.fadeout_speed) + fft * self.fadeout_speed
                else:
                    if self.fadeout_type == 'exponential':
                        tmp = prev_fft[ch] * (1 - self.fadeout_speed)
                    else:
                        tmp = prev_fft[ch] - 10 * self.fadeout_speed
                    fft = np.maximum(tmp, fft)
            if self.additive_type != 'off':
                if self.is_first_frame and self.additive_reset_onfirstframe:
                    prev_additive_fft = None
                fft_for_additive = fft
                if self.additive_type == 'raw':
                    fft_for_additive = fft_before_fadeout
                if type(prev_additive_fft) == list and len(prev_additive_fft) > ch \
                        and np.shape(prev_additive_fft[ch]) == np.shape(fft_for_additive):
                    self.additive_fft.append(np.add(prev_additive_fft[ch], fft_for_additive))
                else:
                    self.additive_fft.append(fft_for_additive)
                # print(self.additive_fft)
            self.last_fft.append(fft)

    def _curve(self, fft_data):
        if not self.aud_filters.use_fake_curve_light:
            return fft_data
        tmp = self._get_curve_mapping_list(len(fft_data))
        return fft_data * tmp

    def _get_curve_mapping_list(self, length):
        mapping = self.aud_filters.fake_curve_light.falloff_curve
        old_version = not hasattr(mapping, "evaluate")  # < 2.82
        curve = mapping.curves[0]
        cache_signature = repr([list(point.location) for point in curve.points])
        if self._curve_mapping_cache_signature == cache_signature:
            return self._curve_mapping_cache
        try:
            if old_version:
                curve.evaluate(1)
            else:
                mapping.evaluate(curve, 1)
        except:
            mapping.initialize()
        if old_version:
            tmp = [curve.evaluate(i / length) for i in range(length)]
        else:
            tmp = [mapping.evaluate(curve, i / length) for i in range(length)]
        self._curve_mapping_cache = tmp
        self._curve_mapping_cache_signature = cache_signature
        return tmp

    def _fake_highpass(self, data):
        if not self.fake_highpass_settings[2]:
            return data
        to = int(self.fake_highpass_settings[0])
        for i in range(to):
            data[i] *= 1 - (to - i) / to * (self.fake_highpass_settings[1])
        return data

    def _midi_multi_note_driver(self, low=None, high=None, ch=None, **kwargs):
        midi_note = kwargs.get("midi", None)
        multi_list = []
        for i in range(midi_note[0], midi_note[1] + 1):
            m_kwargs = kwargs.copy()
            m_kwargs['midi'] = i
            multi_list.append(self.driver(low, high, ch, **m_kwargs))
        if len(midi_note) == 3 and midi_note[2] == 'sum':
            return sum(multi_list)
        elif len(midi_note) == 3 and midi_note[2] in ('avg', 'avg_nonzero'):
            if midi_note[2] == 'avg_nonzero':
                multi_list = [j for j in multi_list if j != 0]
            if len(multi_list) == 0:
                return 0
            return sum(multi_list) / len(multi_list)
        else:
            return max(multi_list)
