"""Fluid Scatter: the torn-apart pieces drift in a small incompressible flow (Navier-Stokes, "stable fluids").

Grid velocity field (N^3, object space, cube around the object) is stepped once per frame:
forces (sound bursts, swirl, curl-noise turbulence, buoyancy) -> viscosity -> vorticity confinement
-> semi-Lagrangian advection -> pressure projection (exact, in Fourier space on a periodic box:
divergence-free, so the flow curls instead of spreading). Pieces are particles carried by the flow (Follow), spun by its vorticity (Spin) and pulled
back to their place - or the morph target - by Return.

No bpy: only numpy. State lives in a Flow object that the scatter cache keeps between frames.
"""
import math

import numpy as np

FORCE_SCALE = .5  # forces -> velocity, in domain half-sizes per second
MAX_SPEED = 6  # domain half-sizes per second
MAX_STEP_FRAMES = 4  # dropped frames are stepped at once, longer jumps reset / use the cache
CACHE_FRAMES = 3000


def _shift(a, axis, offset):
    """Neighbour values with clamped (edge) boundaries."""
    out = np.roll(a, -offset, axis=axis)
    index = [slice(None)] * a.ndim
    index[axis] = -1 if offset > 0 else 0
    out[tuple(index)] = a[tuple(index)]
    return out


def _grad(a, h):
    """Central differences of a scalar grid -> (N, N, N, 3)."""
    return np.stack([(_shift(a, k, 1) - _shift(a, k, -1)) / (2 * h) for k in range(3)], axis=-1)


def curl(v, h):
    d = [[(_shift(v[..., i], k, 1) - _shift(v[..., i], k, -1)) / (2 * h) for k in range(3)] for i in range(3)]
    # d[i][k] = dv_i / dx_k
    return np.stack([d[2][1] - d[1][2], d[0][2] - d[2][0], d[1][0] - d[0][1]], axis=-1)


def divergence(v, h):
    return sum((_shift(v[..., k], k, 1) - _shift(v[..., k], k, -1)) / (2 * h) for k in range(3))


def sample(field, p, lo, h):
    """Trilinear sample of a (N, N, N, C) grid at positions p (M, 3)."""
    n = field.shape[0]
    g = np.clip((p - lo) / h, 0, n - 1.0001)
    i0 = np.floor(g).astype(np.int64)
    f = g - i0
    i1 = np.minimum(i0 + 1, n - 1)
    out = 0
    for dx in (0, 1):
        wx = f[:, 0] if dx else 1 - f[:, 0]
        ix = i1[:, 0] if dx else i0[:, 0]
        for dy in (0, 1):
            wy = f[:, 1] if dy else 1 - f[:, 1]
            iy = i1[:, 1] if dy else i0[:, 1]
            for dz in (0, 1):
                wz = f[:, 2] if dz else 1 - f[:, 2]
                iz = i1[:, 2] if dz else i0[:, 2]
                out = out + field[ix, iy, iz] * (wx * wy * wz)[:, None]
    return out


def periodic_divergence(v, h):
    """Central-difference divergence on a periodic grid (what project() makes zero)."""
    return sum((np.roll(v[..., k], -1, axis=k) - np.roll(v[..., k], 1, axis=k)) / (2 * h) for k in range(3))


def wavenumbers(n, h):
    """Wavenumbers matching central differences (sin(k h) / h), so the projection is exact on the grid."""
    k = np.sin(np.fft.fftfreq(n) * 2 * math.pi) / h
    kv = np.stack(np.meshgrid(k, k, k, indexing='ij'), axis=-1)
    k2 = (kv ** 2).sum(axis=-1)
    k2[k2 == 0] = 1
    return kv, k2


def project(v, kv, k2):
    """Make v divergence-free: remove the gradient part in Fourier space (periodic domain).
    Exact in one pass - no pressure iterations, no leftover compression."""
    spectrum = np.fft.fftn(v, axes=(0, 1, 2))
    spectrum -= kv * ((kv * spectrum).sum(axis=-1) / k2)[..., None]
    return np.fft.ifftn(spectrum, axes=(0, 1, 2)).real


def quat_rotate(q, v):
    """Rotate vectors v (M, 3) by unit quaternions q (M, 4) = (w, x, y, z)."""
    w, u = q[:, :1], q[:, 1:]
    t = 2 * np.cross(u, v)
    return v + w * t + np.cross(u, t)


def quat_integrate(q, omega, dt):
    """q advanced by angular velocity omega (M, 3) over dt."""
    angle = np.linalg.norm(omega, axis=1) * dt
    axis = omega / np.maximum(np.linalg.norm(omega, axis=1, keepdims=True), 1e-9)
    half = angle[:, None] / 2
    dq = np.concatenate([np.cos(half), axis * np.sin(half)], axis=1)
    w1, x1, y1, z1 = dq.T
    w2, x2, y2, z2 = q.T
    out = np.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                    w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                    w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                    w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], axis=1)
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)


class Flow:
    """Grid + particle state of one scattered object."""

    def __init__(self, centers, resolution, domain, seed):
        self.n = int(resolution)
        extent = float(np.abs(centers).max()) if len(centers) else 1.0
        self.half = max(extent, 1e-3) * domain
        self.lo = np.full(3, -self.half)
        self.h = 2 * self.half / (self.n - 1)
        axes = [np.linspace(-self.half, self.half, self.n)] * 3
        self.grid = np.stack(np.meshgrid(*axes, indexing='ij'), axis=-1)  # (N, N, N, 3) cell positions
        self.velocity = np.zeros((self.n, self.n, self.n, 3))
        self.kv, self.k2 = wavenumbers(self.n, self.h)
        rng = np.random.default_rng(seed)
        self.modes = rng.normal(size=(6, 3))  # curl-noise: random Fourier modes of a vector potential
        self.mode_amp = rng.normal(size=(6, 3))
        self.mode_phase = rng.random((6, 3)) * 2 * math.pi
        self.mode_speed = rng.random(6) * 2 - 1
        self.pos = centers.astype(float).copy()
        self.vel = np.zeros_like(self.pos)
        self.rot = np.tile([1.0, 0, 0, 0], (len(centers), 1))
        self.frame = None
        self.history = {}  # frame -> (pos, rot) for scrubbing back over simulated frames

    def signature(self):
        return self.n, round(self.half, 6)

    # ---------------------------------------------------------------- forces

    def turbulence(self, t, scale, speed):
        """Curl of a moving random vector potential: swirly, divergence-free noise (N, N, N, 3)."""
        x = self.grid / max(self.half, 1e-6) * scale
        potential = np.zeros_like(self.grid)
        for k in range(len(self.modes)):
            phase = x @ self.modes[k] + self.mode_speed[k] * speed * t * 2 * math.pi
            potential += np.sin(phase[..., None] + self.mode_phase[k]) * self.mode_amp[k]
        noise = curl(potential, self.h)
        return noise / max(float(np.sqrt((noise ** 2).sum(axis=-1).mean())), 1e-9)  # unit rms

    def reset(self, centers, frame):
        self.velocity[:] = 0
        self.pos = centers.astype(float).copy()
        self.vel = np.zeros_like(self.pos)
        self.rot = np.tile([1.0, 0, 0, 0], (len(centers), 1))
        self.frame = frame
        self.history = {}

    def step(self, p, energy, t, dt, targets, piece_push, flow=1.0):
        """Advance one step. p: fluid settings (fluid_* fields), energy: sound 0..~1, flow: Amount
        (scales every force), targets: where Return pulls each piece, piece_push: per-piece sound kick (M,)."""
        v = self.velocity
        r = np.linalg.norm(self.grid, axis=-1, keepdims=True)
        radial = self.grid / np.maximum(r, 1e-6)
        falloff = np.exp(-(r / max(self.half * .5, 1e-6)) ** 2)
        tangent = np.stack([-self.grid[..., 1], self.grid[..., 0], np.zeros(self.grid.shape[:3])], axis=-1)
        tangent /= np.maximum(np.linalg.norm(tangent, axis=-1, keepdims=True), 1e-6)
        force = radial * falloff * (p.fluid_burst * energy)
        force = force + tangent * falloff * (p.fluid_swirl * (.25 + energy))
        force[..., 2] += p.fluid_buoyancy
        turbulence = p.fluid_turbulence * (1 + p.fluid_audio_turbulence * energy)
        if turbulence > 0:
            force = force + self.turbulence(t, p.fluid_turbulence_scale, p.fluid_turbulence_speed) * turbulence
        v = v + force * (self.half * dt * flow * FORCE_SCALE)
        if p.fluid_viscosity > 0:  # diffusion: blend with the neighbour average
            avg = sum(_shift(v, k, s) for k in range(3) for s in (1, -1)) / 6
            v = v + (avg - v) * min(1.0, p.fluid_viscosity)
        vorticity = p.fluid_vorticity * (1 + p.fluid_audio_vorticity * energy)
        if vorticity > 0:  # vorticity confinement: keep the small swirls alive
            w = curl(v, self.h)
            mag = np.linalg.norm(w, axis=-1)
            g = _grad(mag, self.h)
            g /= np.maximum(np.linalg.norm(g, axis=-1, keepdims=True), 1e-9)
            v = v + np.cross(g, w) * (vorticity * self.h * dt)
        back = self.grid.reshape(-1, 3) - v.reshape(-1, 3) * dt  # semi-Lagrangian advection
        v = sample(v, back, self.lo, self.h).reshape(v.shape)
        v = project(v, self.kv, self.k2)
        v *= max(0.0, 1 - p.fluid_damping * dt)
        speed = np.linalg.norm(v, axis=-1, keepdims=True)
        v *= np.minimum(1.0, MAX_SPEED * self.half / np.maximum(speed, 1e-9))
        self.velocity = v

        # pieces: carried by the flow, kicked by their own sound band, pulled back by Return
        flow_v = sample(v, self.pos, self.lo, self.h)
        follow = 1 - math.exp(-p.fluid_follow * 12 * dt)
        self.vel += (flow_v - self.vel) * follow
        if piece_push is not None:
            out = self.pos / np.maximum(np.linalg.norm(self.pos, axis=1, keepdims=True), 1e-6)
            self.vel += out * (piece_push * flow * p.fluid_burst * self.half * dt)[:, None]
        if p.fluid_return > 0:
            self.vel += (targets - self.pos) * (p.fluid_return * 8 * dt)
            self.vel *= max(0.0, 1 - p.fluid_return * 2 * dt)
        self.pos = self.pos + self.vel * dt
        limit = self.half * 1.5
        self.pos = np.clip(self.pos, -limit, limit)
        if p.fluid_spin > 0:
            omega = sample(curl(v, self.h), self.pos, self.lo, self.h) * (.5 * p.fluid_spin)
            self.rot = quat_integrate(self.rot, omega, dt)
        if p.fluid_return > 0:  # rotate back towards the original orientation
            k = min(1.0, p.fluid_return * 2 * dt)
            ident = np.tile([1.0, 0, 0, 0], (len(self.rot), 1))
            sign = np.where(self.rot[:, :1] < 0, -1.0, 1.0)
            self.rot = self.rot * sign * (1 - k) + ident * k
            self.rot /= np.maximum(np.linalg.norm(self.rot, axis=1, keepdims=True), 1e-12)

    def advance(self, frame, frame_start, frame_end, fps, run_step, keep_on_loop=False):
        """Step from self.frame to frame. Returns False when the caller should reset instead
        (scrubbed back to the start, or a big jump to a frame that wasn't simulated)."""
        if self.frame is not None and frame == self.frame:
            return True
        looped = keep_on_loop and self.frame is not None and frame <= frame_start + MAX_STEP_FRAMES \
            and self.frame >= frame_end - MAX_STEP_FRAMES
        if looped:  # playback wrapped around: keep flowing, forget the old pass
            self.history = {}
            run_step(1.0 / fps)
            self.frame = frame
            return True
        if frame in self.history and (self.frame is None or frame < self.frame):
            self.pos, self.rot = (a.copy() for a in self.history[frame])
            self.frame = frame
            return True
        if frame <= frame_start or self.frame is None or not 0 < frame - self.frame <= MAX_STEP_FRAMES:
            return False
        frames = frame - self.frame
        for _ in range(int(math.ceil(frames))):
            run_step(min(frames, 1.0) / fps)
            frames -= 1
        self.frame = frame
        if frame in self.history or len(self.history) < CACHE_FRAMES:
            self.history[frame] = (self.pos.copy(), self.rot.copy())
        return True

    def vertices(self, rest, centers, pieces, positions=None, scale=1.0):
        """Vertex positions: each piece moved to its particle (or positions) and turned by its rotation.
        scale: one number or one per piece."""
        positions = self.pos if positions is None else positions
        scale = np.asarray(scale, dtype=float)
        rel = (rest - centers[pieces]) * (scale[pieces][:, None] if scale.ndim else scale)
        return positions[pieces] + quat_rotate(self.rot[pieces], rel)
