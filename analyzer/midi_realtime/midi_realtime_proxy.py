import argparse
import sys

parser = argparse.ArgumentParser(description='test')
parser.add_argument('--libs-path', required=False)
parser.add_argument('--input-name', required=True)

args = parser.parse_args()
if getattr(args, 'libs_path') is not None:
    sys.path.append(args.libs_path)

import mido

mido.set_backend('mido.backends.pygame')

sys.stdout.flush()

input = mido.open_input(name=args.input_name)

try:
    while True:
        msg = input.receive()
        if msg.type == 'control_change':
            print(msg.channel + 1, "c{}".format(msg.control), msg.value)
            sys.stdout.flush()
        elif msg.type in ('note_on', 'note_off'):
            velocity = msg.velocity if msg.type == 'note_on' else 0
            print(msg.channel + 1, msg.note, velocity)
            sys.stdout.flush()

except Exception as e:
    print('ERROR', e)
