"""Morph target for Scatter: every piece of mesh A gets a place on the surface of
mesh B. At morph 1 the shards of A rebuild the shape of B.

Pieces and target points are paired by sorting both along a Morton (Z-order)
curve of their bounding-box-normalized positions, so neighbours stay neighbours
and pieces don't cross the whole shape."""
import numpy as np


def sample_surface(mesh, matrix, n, seed):
    """n area-weighted random points (and normals) on a mesh, transformed by matrix (4x4)."""
    mesh.calc_loop_triangles()
    tri_count = len(mesh.loop_triangles)
    if not tri_count or not n:
        return None
    co = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", co)
    m = np.array(matrix)
    co = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
    tris = np.empty(tri_count * 3, dtype=np.int32)
    mesh.loop_triangles.foreach_get("vertices", tris)
    a, b, c = (co[tris.reshape(-1, 3)[:, k]] for k in range(3))
    cross = np.cross(b - a, c - a)
    area = np.linalg.norm(cross, axis=1) / 2
    total = area.sum()
    if total <= 0:
        return None
    rng = np.random.default_rng(seed)
    pick = rng.choice(tri_count, size=n, p=area / total)
    u, v = rng.random(n), rng.random(n)
    flip = u + v > 1
    u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
    points = a[pick] + (b[pick] - a[pick]) * u[:, None] + (c[pick] - a[pick]) * v[:, None]
    normals = cross[pick] / np.maximum(np.linalg.norm(cross[pick], axis=1, keepdims=True), 1e-12)
    return points, normals, total


def morton_rank(points):
    lo, hi = points.min(axis=0), points.max(axis=0)
    q = ((points - lo) / np.maximum(hi - lo, 1e-9) * 1023).astype(np.uint64)
    code = np.zeros(len(points), dtype=np.uint64)
    for bit in range(10):
        for axis in range(3):
            code |= ((q[:, axis] >> np.uint64(bit)) & np.uint64(1)) << np.uint64(3 * bit + axis)
    return np.argsort(code, kind='stable')


def match(sources, targets):
    """Index into targets for every source point."""
    out = np.empty(len(sources), dtype=np.int64)
    out[morton_rank(sources)] = morton_rank(targets)
    return out


def build(target_obj, owner_matrix, centers, piece_normals, piece_area_total, seed):
    """Per-piece target center, rotation (axis, angle) from the piece normal to the
    target normal, and the scale that makes A's total area match B's."""
    if target_obj is None or target_obj.type != 'MESH':
        return None
    to_local = np.linalg.inv(np.array(owner_matrix)) @ np.array(target_obj.matrix_world)
    sampled = sample_surface(target_obj.data, to_local, len(centers), seed)
    if sampled is None:
        return None
    points, normals, area = sampled
    idx = match(centers, points)
    points, normals = points[idx], normals[idx]
    has_normal = np.linalg.norm(piece_normals, axis=1) > .5
    axis = np.cross(piece_normals, normals)
    length = np.linalg.norm(axis, axis=1)
    angle = np.where(has_normal, np.arctan2(length, np.sum(piece_normals * normals, axis=1)), 0)
    fallback = np.where(np.abs(piece_normals[:, 0:1]) < .9, [[1.0, 0, 0]], [[0, 1.0, 0]])
    axis = np.where(length[:, None] > 1e-9, axis / np.maximum(length, 1e-9)[:, None],
                    np.cross(piece_normals, fallback) + [[0, 0, 1e-9]])
    axis /= np.maximum(np.linalg.norm(axis, axis=1, keepdims=True), 1e-9)
    fit = float(np.sqrt(area / piece_area_total)) if piece_area_total > 0 else 1.0
    return {"centers": points, "axis": axis, "angle": angle, "fit": fit}
