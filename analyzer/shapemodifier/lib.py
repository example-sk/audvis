from random import Random

from ...note_calculator import calculate_note


def set_value(arr, index, value, operation):
    if operation == 'add':
        arr[index] += value
    elif operation == 'set':
        arr[index] = value


def calc_driver_value(settings, driver, index, weight=1):
    if settings.freq_seq_type == 'notes':
        freq_from = calculate_note((index + settings.note_offset) * settings.note_step, settings.note_a4_freq)
        freq_to = calculate_note((index + settings.note_offset + 1) * settings.note_step, settings.note_a4_freq)
    elif settings.freq_seq_type == 'classic':
        rng = settings.freqrange
        freqstep = settings.freq_step_calc
        freqstart = settings.freqstart
        freq_from = index * freqstep + freqstart
        freq_to = index * freqstep + rng + freqstart

    if settings.freq_seq_type == 'midi':
        driver_value = driver(midi=index + settings.midi.offset,
                              ch=settings.midi.channel,
                              track=settings.midi.track,
                              file=settings.midi.file,
                              device=settings.midi.device)
    else:
        send_kwargs = {}
        if settings.sound_sequence != '':
            send_kwargs['seq'] = settings.sound_sequence
        driver_value = driver(freq_from, freq_to, ch=settings.channel, **send_kwargs)
    add = settings.add
    if weight == 0:
        return 0
    val = (driver_value + add / settings.factor) * settings.factor * weight
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
