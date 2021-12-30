import re

from ...note_calculator import calculate_note


def build_expression(props, add=0.0, iterations_add=0):
    rangeperobject = props.freqrange
    freqstart = props.freqstart
    if props.freq_step_enable:
        freq_step = props.freq_step
    else:
        freq_step = rangeperobject
    index = props.iteration + iterations_add
    if props.freq_seq_type == 'midi':
        expr_kwargs = 'midi={}'.format((index + props.midi.offset) % 128)
        if props.midi.file != '':
            expr_kwargs += ', file=' + repr(props.midi.file)
        if props.midi.track != '':
            expr_kwargs += ', track=' + repr(props.midi.track)
        if props.midi.channel != 'all' and props.midi.channel != '':
            expr_kwargs += ', ch=' + repr(props.midi.channel)
        if props.midi.device != '':
            expr_kwargs += ', device=' + repr(props.midi.device)
        args = expr_kwargs
    else:
        if props.freq_seq_type == 'notes':
            freq_from = calculate_note((index + props.note_offset) * props.note_step,
                                       props.note_a4_freq)
            freq_to = calculate_note((index + props.note_offset + 1) * props.note_step,
                                     props.note_a4_freq)
        else:
            freq_from = index * freq_step + freqstart
            freq_to = freq_from + rangeperobject
        args = "{:.6}, {:.6}".format(freq_from, freq_to)
        if props.sound_sequence != '':
            args += ', seq=' + repr(props.sound_sequence)
        if props.channel != 1:
            args += ', ch={}'.format(props.channel)
        if props.additive:
            args += ', additive=True'

    main_expr = "audvis({})".format(args)
    if props.factor != 1.0:
        main_expr += " * {:.6}".format(props.factor)

    result = props.expression
    result = re.sub(r'\bindex\b', str(props.iteration), result)
    result = result.replace("audvis()", main_expr)
    if add + props.add != 0.0:
        result = "{:.6} + {}".format((add + props.add) * 1.0, result)
    return result
