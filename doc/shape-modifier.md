# Shape Modifier

Shape modifier is used to animate all vertices / points of meshes, curves, surfaces, grease pencils or lattices. Animate
by sound (or midi), of course.

Internally, shape modifier calls the same function like the one used for [driver expressions](./drivers.md) many times.

In case of mesh, curve, surface or lattice objects, two Shape Keys are created - one named "AudVis Shape Origin" and the
second one "AudVis Shape Target". For every frame, relevant data is copied from "AudVis Shape Origin" into "AudVis Shape
Target", and modified the way we want.

In case of grease pencil objects, there are two frames used - frame 0, which will be copied and modified by sound into
frame 1. **Warning**: if you have animated grease pencil with data on multiple frames, AudVis will damage it and keep
only one frame from your original data.

## Settings

- **Enable** - (in the Shape Modifier panel header): do you want to use Shape Modifiers? If not, keep this disabled
- **Enable** for single selected object - every object of supported type is animated separately if enabled
- **Animation Type**
    - **Normal** - in reality, object normal. Move vertices / points away from center of the object. Best in case of
      circles or spheres.
    - **Location Z** - moves vertices / points along the Z axis. Best for use with grid mesh
    - **Location** - additional setting **Vector** appears. Here you can setup the direction the points will move
    - **Track to object** - move all vertices / points towards the center of a selected object in the **Target**
      property
    - **Vertex Group Weight** - creates two vertex groups - "AudVis Origin" and "AudVis Target". You can then use the
      "AudVis Target" vertex group for example in the Displace Modifier, or in geometry nodes, or almost anywhere you
      want.
    - **UV Map** - creates two UV maps - "audvis from" and "audvis to" and moves the points in the map. Not sure if this
      is ever useful
    - **Vertex Color** - creates two Vertex Colors - "audvis from" and "audvis to". You can use the "audvis to" in the
      shading nodes, or geometry nodes
    - **Curve Radius** (only for curve objects) - useful for example when you have `Geometry -> Bevel -> Depth`, but
      also in some other cases
    - **Curve Tilt** (only for curve objects) - useful for example if you have `Geometry -> Extrude`
      or `Geometry -> Bevel -> Object`
- **Operation Type**
    - **Add** - adds value to existing value in "audvis from" / "AudVis Origin"
    - **Set** - just sets the value received from the analyzer
- **Multiple Freq properties** - the whole concept is [described here](./freq-sequencing.md)
- **Factor** - multiply received values by this number
- **Add** - add this number to received values
- **Order** - if you want to see vertices order, go to Blender preferences, enable `Interface -> Developer Extras` and
  then in the 3D Viewport enable `Overlays menu -> Developer -> Indices`
    - **1,2,3...** - ascending order
    - **...3,2,1** - descending order
    - **random** - random order
- **Use Vertex Group** (only for mesh objects) - if enabled, a new vertex group is created - "AudVis Location Weight"
  (not the best name for this use, sorry...). Vertices removed from this vertex group will be skipped. Other vertices
  will be affected by shape modifier by the weight set in this "AudVis Location Weight" vertex group. If a weight of a
  vertex is 0.2, the value will be multiplied by 0.2. Of course, you can use Weight Paint.
- **Bake Shape Modifier** - the whole animation will be baked into animation data, so you can render your animation on a
  render farm or different computer where you don't have AudVis installed.
- **Clean Data** - deleted all the relevant shape keys, vertex groups and vertex colors