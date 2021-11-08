a = 2 ** (1 / 12)


def calculate_note(distance_from_a4, a4=440):
    return a4 * (a ** distance_from_a4)
