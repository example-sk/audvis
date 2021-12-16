# Concept: Frequency Sequencing

[Shape Modifier](./shape-modifier.md), [Spectrogram](./spectrogram.md), [Generate Example Objects](./example-objects.md)
, [Generate Armature](./armature.md) use the same concept. AudVis iterates over a list of points/bones/objects and moves
them somehow. Here is explanation.

For simplicity, word "point" is used here, but it means vertex, face, object, bone or whatever is correct in the
context.

## Settings

- **Freq Sequencing**
    - **Linear**
        - **Frequency Range Per Point** - if set to 50, every item will be animated by range of 50Hz. For example first
          point will be animated by 0-50Hz, second one (according to other settings) 50-100Hz or 10-60Hz... and so on
        - **Frequency Start** - how many Hz to skip. If set to 200, first point will be animated for example by
          200-250Hz
        - **Set Custom Step** and **Frequency Step**
            - if disabled, the sequence will be 0-50Hz, 50-100Hz, 100-150Hz...
            - if enabled and the Step set to 10, the sequence will be: 0-50Hz, 10-60Hz, 20-70Hz...
    - **Notes** - [wiki](https://en.wikipedia.org/wiki/Piano_key_frequencies)
        - **A4 Note Frequency** - default 440Hz, but you can set it to whatever you want
        - **Note Step** - if you have a lot of points to animate, you probably want to lower this number. If not, keep
          it on 1.0
        - **Note Step Offset** - on what note you want to start - affected by **Note Step**. If you have a lot of bass,
          you probably want to use negative values for this property
    - **MIDI Notes** - every point is 1 midi note
        - **MIDI Note Offset** - if you are interested only in notes higher than 40, set this property to 40
    - There is also one line telling you what sequences you will get in your animation. For example 0.00 - 4,150.00 Hz.
      If you see too high numbers here, for example over 20 000 Hz, you want to change your settings to get lower
      number. If your sound input's sampling frequency is 44100 Hz, FFT used by AudVis can't give you numbers over
      22050Hz (sampling frequency / 2). 