import argparse
import sys

parser = argparse.ArgumentParser(description='test')
parser.add_argument('--libs-path', required=False)

args = parser.parse_args()
if getattr(args, 'libs_path') is not None:
    sys.path.append(args.libs_path)

import mido
mido.set_backend('mido.backends.pygame')
lst = mido.get_input_names()
print("---- delimiter ----")
for input_name in lst:
    print(input_name)
sys.stdout.flush()