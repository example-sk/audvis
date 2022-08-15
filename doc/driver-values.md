# Driver Values panel

[Realtime](./realtime.md) and [Sequence](./sequence.md) analyzers produce data. In Driver Values you can tweak them.

## Settings:

- if **Use Better Filters** is disabled (default):
    - **Highpass Frequency** and **Highpass Strength** - a
- if **Use Better Filters** is enabled:
    - before FFT is performed, current sound chunk data is loaded into `aud.Sound` object and then these things are
      applied:
    - **Highpass Frequency** and **Q** - [highpass](https://docs.blender.org/api/current/aud.html#aud.Sound.highpass)
    - **Lowpass Frequency** and **Q** - [lowpass](https://docs.blender.org/api/current/aud.html#aud.Sound.lowpass)
    - **Attack, Decay, Sustain, Release** - [ADSR](https://docs.blender.org/api/current/aud.html#aud.Sound.ADSR)
    - **Use Curve** - if enabled, you can make your own highpass and lowpass filter - left part of the curve is for
      lower frequencies, right part of the curve is for highest frequencies
- **Factor** - all values will be multiplied by this value
- **Max** - doesn't allow values higher than this
- **Add** - adds this number to all calculated values
- **Add Noise** - adds
- **Normalize Values** - just try it, I don't know
- **Fade Out Type**:
    - **Off** - don't fade out
    - **Linear** - returns higher value of "previous frame value - **Fade Out Speed**" or "current value"
    - **Exponential** - returns higher value of "previous frame value * (1 - **Fade Out Speed**)" or "current value"
    - **Natural** - similar to exponential, but much more natural results. The formula is 
      - `previous_fft * (1 - fadeout_speed) + fft * fadeout_speed`
    - warning: if you jump between frames, the results can be inconsistent