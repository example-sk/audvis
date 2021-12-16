# UPBGE

You can use AudVis Real Time Analyzer and Midi Realtime in UPBGE.

In the N-panel of the Logic Bricks Editor, and in the Game Object Properties, there are some buttons for AudVis. After
creating a component, you can set its properties in the Game Object Properties (icon just over Material Properties).

- **Logic setup**:
    - **Create Action Logic** - generates connected Sensor, Controller and Actuator. After doing this, you have to setup
      the created Action - set the Property and Action
- **Register Component**:
    - **Updater** - you need at least one AudVis call per every frame. If you only want to use the Shape Modifier or
      Spectrogram, use this component
    - **Realtime Sound** - creates a game property and periodically sets the value by the current sound frequencies
        - **freq_from** and **freq_to** - look for [driver expressions](./drivers.md)
        - **factor** - multiply the result value
        - **add** - add to the result value
    - **Midi Realtime** - creates a game property and periodically sets the value by the current midi state
        - **note** - MIDI note which you want to react to
        - **factor** - multiply the result value
        - **add** - add to the result value