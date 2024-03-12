from random import Random

from ...note_calculator import calculate_note
import math


def set_value(arr, index, value, operation):
    if operation == 'add':
        arr[index] += value
    elif operation == 'set':
        arr[index] = value


def calc_driver_value(props, driver, index, weight=1):
    freq_from = 0
    freq_to = 0
    if props.freq_seq_type == 'notes':
        freq_from = calculate_note((index + props.note_offset) * props.note_step, props.note_a4_freq)
        freq_to = calculate_note((index + props.note_offset + 1) * props.note_step, props.note_a4_freq)
    elif props.freq_seq_type == 'classic':
        rng = props.freqrange
        freqstep = props.freq_step_calc
        freqstart = props.freqstart
        freq_from = index * freqstep + freqstart
        freq_to = index * freqstep + rng + freqstart

    if props.freq_seq_type == 'midi':
        driver_value = driver(midi=index + props.midi.offset,
                              ch=props.midi.channel,
                              track=props.midi.track,
                              file=props.midi.file,
                              device=props.midi.device)
    else:
        send_kwargs = {}
        if props.sound_sequence != '':
            send_kwargs['seq'] = props.sound_sequence
        if props.sequence_channel > 0:
            send_kwargs['seq_channel'] = props.sequence_channel
        if props.additive == 'off':
            driver_value = driver(freq_from, freq_to, ch=props.channel, **send_kwargs)
        else:
            tmp_val = driver(freq_from, freq_to, ch=props.channel, additive=True, **send_kwargs)
            if props.additive in ('sin', 'sin2'):
                tmp_val = math.sin(tmp_val * props.additive_phase_multiplier + props.additive_phase_offset)
                if props.additive == 'sin2':
                    tmp_val = tmp_val / 2 + .5  # values range from 0 to 1
            elif props.additive == 'mod':
                tmp_val = (tmp_val * props.additive_phase_multiplier + props.additive_phase_offset) \
                          % props.additive_modulus
            elif props.additive == 'on':
                pass
            driver_value = tmp_val
    add = props.add
    if weight == 0 or props.factor == 0:
        return 0
    val = (driver_value + add / props.factor) * props.factor * weight
    # print(index, val, freq_from, freq_to)
    return val


def sorted_freq_indexes(settings, count):
    freq_indexes = list(range(count))
    order = settings.order
    if order == 'asc':
        pass
    elif order == 'desc':
        freq_indexes = freq_indexes[::-1]
    elif order == 'rand':
        seed = settings.random_seed
        Random(seed).shuffle(freq_indexes)
    return freq_indexes


class location_setter:
    @staticmethod
    def vector(arr, index, vector, operation):
        set_value(arr, index * 3 + 0, vector[0], operation)
        set_value(arr, index * 3 + 1, vector[1], operation)
        set_value(arr, index * 3 + 2, vector[2], operation)

    @staticmethod
    def track_to(locations, i, vertex_co, val, this_obj, settings, operation):
        target_relative_location = this_obj.matrix_world.inverted() @ settings.track_object.location
        vector = (target_relative_location - vertex_co).normalized() * val
        set_value(locations, i * 3 + 0, vector[0], operation)
        set_value(locations, i * 3 + 1, vector[1], operation)
        set_value(locations, i * 3 + 2, vector[2], operation)
