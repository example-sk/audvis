from ..note_calculator import calculate_note


def hz_label(start, range_per_point, step, points_count):
    return "{:,.2f} - {:,.2f} Hz ".format(
        start,
        start + (points_count - 1) * step + range_per_point
    )


# https://pages.mtu.edu/~suits/NoteFreqCalcs.html
def notes_label(count=1, step=1, a4=440, note_steps_offset=50):
    start_freq = calculate_note(note_steps_offset * step, a4)
    end_freq = calculate_note((count + note_steps_offset) * step, a4)
    # print([count, start_freq, end_freq])
    return "{:,.2f} - {:,.2f} Hz".format(
        start_freq,
        end_freq
    )
