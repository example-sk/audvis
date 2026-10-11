"""Small adapters for legacy Grease Pencil and Blender 4.3+ drawings."""


def is_grease_pencil(obj):
    return obj is not None and obj.type in {'GPENCIL', 'GREASEPENCIL'}


def data_collection(data):
    # 4.3/4.4 keep legacy annotation data in grease_pencils; newer releases
    # expose the new object data under grease_pencils again.
    if hasattr(data, 'grease_pencils_v3'):
        return data.grease_pencils_v3
    return data.grease_pencils


def strokes(frame):
    if hasattr(frame, 'drawing'):
        return frame.drawing.strokes
    return frame.strokes


def remove_frame(layer, frame):
    if hasattr(frame, 'drawing'):
        layer.frames.remove(frame.frame_number)
    else:
        layer.frames.remove(frame)


def move_frame(layer, frame, number):
    if hasattr(frame, 'drawing'):
        return layer.frames.move(frame.frame_number, number)
    frame.frame_number = number
    return frame


def copy_drawing_frame(layer, source, number):
    """Copy all drawing attributes without sharing mutable source geometry."""
    for frame in layer.frames:
        if frame.frame_number == number:
            remove_frame(layer, frame)
            break
    return layer.frames.copy(source.frame_number, number, instance_drawing=False)


def add_contours(frame, contours, radius=0.02):
    contours = [contour for contour in contours if len(contour)]
    if hasattr(frame, 'drawing'):
        drawing = frame.drawing
        if not contours:
            return
        drawing.add_strokes([len(contour) for contour in contours])
        # Obtain stroke slices only after changing the drawing topology.
        for stroke, contour in zip(drawing.strokes, contours):
            for point, co in zip(stroke.points, contour):
                point.position = co
                point.radius = radius
                point.opacity = 1.0
        drawing.tag_positions_changed()
    else:
        for contour in contours:
            stroke = frame.strokes.new()
            stroke.points.add(len(contour))
            for point, co in zip(stroke.points, contour):
                point.co = co
