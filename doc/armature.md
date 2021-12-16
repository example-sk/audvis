# Armature Generator

This feature gets **selected** faces of your **mesh** object, and creates a new armature object + a new Armature
modifier on the original mesh object. All the created bones will be animated along the face's normal, thus move the face
along its normal. This is done by creating a driver for the location Y for every single created bone. With default
settings, one of the bones will have a driver expression like this `audvis(450.0, 500.0) * 0.1`

Video: [![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/e0v9dO3wU1s/0.jpg)](https://www.youtube.com/watch?v=e0v9dO3wU1s)

## Settings:

- **Inset** - performs also "Inset Faces" on all the selected faces. Only the new created faces will be animated.
    - **Extrude After Inset** - after "Inset Faces", also "Extrude" will be performed. Only the new faces after
      extruding will be animated
    - **Inset Size** - this is the same like "Thickness" property of the "Inset Faces" operator.
- **Multiple Freq properties** - the whole concept is [described here](./freq-sequencing.md)
- **Keep Old Vertex Groups**
    - if disabled, for every clicking on Generate AudVis Armature, AudVis will delete all the vertex groups with names
      starting with AudvisArm
    - if enabled, only new vertex groups will be created, so you can use the same armature, but add new animated bones.
      In this case, don't forget to set **Frequency Start**
- **Generate AudVis Armature** - perform the generating process. Please, always save your project before doing this, so
  you can easily return to previous state in case you don't like the result. Mainly if using Inset and Extrude.