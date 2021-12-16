# UPBGE

You can use AudVis Real Time Analyzer and Midi Realtime in UPBGE.

In the N-panel of the Logic Bricks Editor, there are some buttons for AudVis

- **Logic setup**:
    - **Create Action Logic** - generates connected Sensor, Controller and Actuator. After doing this, you have to setup the created Action - set the Property and Action 
- **Register Component**:
    - **Updater** - you need at least one AudVis call per every frame. If you only want to use the Shape Modifier or Spectrogram, use this component
    - **Realtime Sound** - creates a game property and periodically sets the value by the current sound frequencies
    - **Midi Realtime** - creates a game property and periodically sets the value by the current midi state 