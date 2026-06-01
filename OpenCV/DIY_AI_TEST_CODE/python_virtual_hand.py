"""
python_virtual_hand.py  -  InMoov Cybernetic Arm 3D Simulator
==============================================================
Renders a stunning 3D sci-fi robotic arm with metallic shading,
glowing joints, an Arc Reactor core, animated HUD telemetry,
and a full forearm section.

Interface:
    init_virtual_hand()               -> starts the renderer thread
    send_to_virtual_hand(commands)    -> pushes servo angles dict
"""

import pygame
import sys
import math
import threading

# ═══════════════════════════════════════════════════════════════
#  SERVO CONFIGURATION  (must match STATICMODE.py)
# ═══════════════════════════════════════════════════════════════

SERVO_CONFIG = {
    "Thumb":  {"min": 175, "max": 285},
    "Index":  {"min": 90,  "max": 290},
    "Middle": {"min": 100, "max": 290},
    "Ring":   {"min": 100, "max": 290},
    "Pinky":  {"min": 85,  "max": 290},
    "Wrist":  {"min": 0,   "max": 300},
}

FINGER_ORDER = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

# ═══════════════════════════════════════════════════════════════
#  WINDOW
# ═══════════════════════════════════════════════════════════════

WIN_W, WIN_H = 960, 720
FPS = 60

# ═══════════════════════════════════════════════════════════════
#  ARM LAYOUT  (tweak these to reposition the arm)
# ═══════════════════════════════════════════════════════════════

ARM_CX     = 610       # Center X of the palm (perfectly centered on right panel)
ARM_CY     = 330       # Center Y of the palm (given breathing room from header)
HAND_SCALE = 1.20      # Overall arm size multiplier

# ═══════════════════════════════════════════════════════════════
#  PREMIUM DARK VICTORIAN STEAMPUNK / SCI-FI COLOR PALETTE
# ═══════════════════════════════════════════════════════════════

# Background layers
BG             = (10, 8, 6)         # Deep charcoal walnut
GRID           = (25, 20, 15)       # Burnished copper grid
PANEL          = (16, 12, 9)        # Dark mahogany inlay
PANEL_BORDER   = (65, 45, 30)       # Aged brass border

# Metallic shading system (dark -> light for 3D bevel effect)
METAL_SHADOW   = (8, 6, 4)
METAL_DARK     = (28, 20, 14)       # Cast iron
METAL_BASE     = (135, 95, 40)      # Polished brass base
METAL_MID      = (165, 125, 60)     # Brass mid
METAL_LIGHT    = (195, 155, 80)     # Bright brass
METAL_HIGHLIGHT= (235, 195, 120)    # Burnished gold highlight
METAL_SPECULAR = (255, 230, 180)    # Specular gold reflection

# Steam & Clockwork Neon Glow - EMERALD GREEN GASLIGHT
EMERALD        = (0, 220, 100)      # Gaslight emerald glow
EMERALD_MID    = (0, 140, 60)       # Rich jade filament
EMERALD_DIM    = (0, 70, 30)        # Soft moss embers
EMERALD_GLOW   = (0, 35, 15)        # Boiler gas chamber glow
MAGENTA        = (230, 40, 90)      # Rose gold accent
GREEN          = (0, 210, 110)      # Saturated gaslight green
ORANGE         = (255, 110, 0)      # Boiler fire
RED            = (220, 30, 30)      # High pressure warning
WHITE          = (225, 255, 235)    # Warm incandescent cream with green tint
TEXT           = (205, 235, 215)    # Green-ivory text
TEXT_DIM       = (110, 135, 120)    # Soft mossy dust

# Map existing theme names to Victorian Emerald Gaslight colors for seamless update
CYAN           = EMERALD
CYAN_MID       = EMERALD_MID
CYAN_DIM       = EMERALD_DIM
CYAN_GLOW_COL  = EMERALD_GLOW

# ═══════════════════════════════════════════════════════════════
#  ARM GEOMETRY
# ═══════════════════════════════════════════════════════════════

FINGER_SEGMENTS = {
    "Thumb":  [44, 34, 26],
    "Index":  [60, 44, 32],
    "Middle": [64, 47, 34],
    "Ring":   [58, 42, 32],
    "Pinky":  [47, 34, 24],
}

# Pixel offsets from palm center to each finger root (symmetrical human mirrored layout)
FINGER_ANCHORS = {
    "Thumb":  ( 60,  20),
    "Index":  ( 42, -54),
    "Middle": ( 14, -60),
    "Ring":   (-14, -60),
    "Pinky":  (-42, -48),
}

# Resting angle for each finger (degrees, 0 = right, 90 = up) - mirrored straight fan
FINGER_BASE_ANGLES = {
    "Thumb":   40,
    "Index":   78,
    "Middle":  90,
    "Ring":   102,
    "Pinky":  114,
}

# Segment widths (start, end) — tapers from proximal to distal
SEGMENT_WIDTHS = [
    (14, 11),   # proximal phalanx
    (11,  8),   # middle phalanx
    ( 8,  5),   # distal phalanx
]

JOINT_RADII = [12, 10, 8, 6]   # base -> tip

# ═══════════════════════════════════════════════════════════════
#  THREAD-SAFE SHARED STATE
# ═══════════════════════════════════════════════════════════════

_lock         = threading.Lock()
_servo_angles = {f: SERVO_CONFIG[f]["min"] for f in SERVO_CONFIG}
_servo_angles["Wrist"] = 150.0  # Center position for 0-300 range
_servo_angles.update({f"{f}_Spread": 0.0 for f in FINGER_ORDER})
_mode         = "MANUAL"
_flipped      = False  # Toggle with [F] to mirror hand horizontally


def send_to_virtual_hand(servo_commands: dict):
    """Push new servo angles from the tracking pipeline."""
    global _mode
    with _lock:
        for component, angle in servo_commands.items():
            if component in _servo_angles:
                _servo_angles[component] = float(angle)
        _mode = "LIVE"


def init_virtual_hand():
    """Launch the renderer on a daemon thread."""
    t = threading.Thread(target=_run_pygame, daemon=True)
    t.start()
    return t


# ═══════════════════════════════════════════════════════════════
#  MATH HELPERS
# ═══════════════════════════════════════════════════════════════

def rotate_point(point, angle_deg, center):
    """Rotate *point* around *center* by *angle_deg* degrees."""
    rad = math.radians(angle_deg)
    px, py = point
    cx, cy = center
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    qx = cx + cos_a * (px - cx) - sin_a * (py - cy)
    qy = cy + sin_a * (px - cx) + cos_a * (py - cy)
    return (int(qx), int(qy))


def servo_to_curl(angle, finger_name):
    """Map a servo angle to a 0-1 curl fraction."""
    cfg = SERVO_CONFIG[finger_name]
    span = max(cfg["max"] - cfg["min"], 1)
    return max(0.0, min(1.0, (angle - cfg["min"]) / span))


# ═══════════════════════════════════════════════════════════════
#  GLOW CACHE  (pre-render once, blit many times = fast)
# ═══════════════════════════════════════════════════════════════

_glow_cache: dict = {}


def _get_glow(radius, color=CYAN):
    """Return a cached radial-glow surface."""
    key = (radius, color[:3])
    if key not in _glow_cache:
        size = radius * 6
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        for r in range(radius * 3, 0, -2):
            a = max(0, int(38 * (1.0 - r / (radius * 3))))
            pygame.draw.circle(surf, (*color[:3], a), (cx, cy), r)
        _glow_cache[key] = surf
    return _glow_cache[key]


# ═══════════════════════════════════════════════════════════════
#  3-D SEGMENT RENDERER
# ═══════════════════════════════════════════════════════════════

def _draw_3d_segment(surface, p1, p2, w1, w2):
    """
    Draw a metallic 3-D-looking arm bone between p1 and p2.
    Layers: shadow -> dark base -> metallic panel -> highlight -> circuit -> border.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 1:
        return

    # perpendicular unit vector
    nx, ny = -dy / length, dx / length

    # Quad corners
    tl = (p1[0] + nx * w1, p1[1] + ny * w1)
    bl = (p1[0] - nx * w1, p1[1] - ny * w1)
    br = (p2[0] - nx * w2, p2[1] - ny * w2)
    tr = (p2[0] + nx * w2, p2[1] + ny * w2)
    outer = [(int(x), int(y)) for x, y in (tl, tr, br, bl)]

    # 1. Drop shadow (offset +3, +3)
    shadow = [(x + 3, y + 3) for x, y in outer]
    pygame.draw.polygon(surface, METAL_SHADOW, shadow)

    # 2. Dark metal base
    pygame.draw.polygon(surface, METAL_DARK, outer)

    # 3. Inset lighter metallic panel (bevel)
    cx_a = sum(x for x, _ in outer) / 4
    cy_a = sum(y for _, y in outer) / 4
    inner = [(int(cx_a + (x - cx_a) * 0.78),
              int(cy_a + (y - cy_a) * 0.78)) for x, y in outer]
    pygame.draw.polygon(surface, METAL_BASE, inner)

    # 4. Specular highlight (top edge)
    pygame.draw.line(surface, METAL_HIGHLIGHT, outer[0], outer[1], 1)

    # 5. Circuit filament through the centre
    m1 = (int((tl[0] + bl[0]) / 2), int((tl[1] + bl[1]) / 2))
    m2 = (int((tr[0] + br[0]) / 2), int((tr[1] + br[1]) / 2))
    pygame.draw.line(surface, CYAN_DIM, m1, m2, 1)

    # 6. Cyan border
    pygame.draw.polygon(surface, CYAN_MID, outer, 1)


# ═══════════════════════════════════════════════════════════════
#  JOINT RENDERER
# ═══════════════════════════════════════════════════════════════

def _draw_joint(surface, pos, radius, glow=True):
    """Draw a glowing mechanical pivot joint."""
    x, y = int(pos[0]), int(pos[1])

    # glow aura
    if glow and radius >= 6:
        g = _get_glow(radius)
        gw, gh = g.get_size()
        surface.blit(g, (x - gw // 2, y - gh // 2),
                     special_flags=pygame.BLEND_ADD)

    # outer ring
    pygame.draw.circle(surface, METAL_DARK, (x, y), radius)
    pygame.draw.circle(surface, CYAN_MID, (x, y), radius, 1)

    # inner core
    cr = max(2, radius - 4)
    pygame.draw.circle(surface, CYAN, (x, y), cr)
    pygame.draw.circle(surface, WHITE, (x, y), max(1, cr - 3))


def _draw_fingertip(surface, pos, color, tick):
    """Pulsing colour-coded fingertip sensor."""
    x, y = int(pos[0]), int(pos[1])
    pulse = 0.75 + 0.25 * math.sin(tick * 0.08)
    r = int(7 * pulse)
    pygame.draw.circle(surface, color, (x, y), r + 4, 1)
    pygame.draw.circle(surface, color, (x, y), r)
    pygame.draw.circle(surface, WHITE, (x, y), max(1, r - 3))


def _draw_gear(surface, cx, cy, radius, num_teeth, angle_deg, color_teeth, color_ring):
    """Draws a beautiful Victorian brass gear with rotating teeth."""
    pygame.draw.circle(surface, color_ring, (cx, cy), radius)
    pygame.draw.circle(surface, METAL_DARK, (cx, cy), int(radius * 0.65))
    pygame.draw.circle(surface, color_ring, (cx, cy), int(radius * 0.25))
    
    # Gear Teeth
    for i in range(num_teeth):
        rad = math.radians(i * (360 / num_teeth) + angle_deg)
        r1 = radius - 2
        r2 = radius + 6
        x1 = cx + int(r1 * math.cos(rad))
        y1 = cy + int(r1 * math.sin(rad))
        x2 = cx + int(r2 * math.cos(rad))
        y2 = cy + int(r2 * math.sin(rad))
        pygame.draw.line(surface, color_teeth, (x1, y1), (x2, y2), 4)


# ═══════════════════════════════════════════════════════════════
#  ARM COMPONENTS
# ═══════════════════════════════════════════════════════════════

def _draw_forearm(surface, cx, cy, tick):
    """Stationary armored forearm extending from below the palm."""
    wrist_y  = cy + 75
    bottom_y = cy + 280
    w_top    = int(40 * HAND_SCALE)
    w_bot    = int(54 * HAND_SCALE)

    pts = [
        (cx - w_top, wrist_y),
        (cx + w_top, wrist_y),
        (cx + w_bot, bottom_y),
        (cx - w_bot, bottom_y),
    ]

    # shadow
    shadow = [(x + 4, y + 4) for x, y in pts]
    pygame.draw.polygon(surface, METAL_SHADOW, shadow)

    # base
    pygame.draw.polygon(surface, METAL_DARK, pts)

    # inner metallic panel
    cxa = sum(x for x, _ in pts) / 4
    cya = sum(y for _, y in pts) / 4
    inner = [(int(cxa + (x - cxa) * 0.86),
              int(cya + (y - cya) * 0.93)) for x, y in pts]
    pygame.draw.polygon(surface, METAL_BASE, inner)

    # Rotating clockwork brass gear inside forearm window
    gear_y = int((wrist_y + bottom_y) / 2)
    _draw_gear(surface, cx, gear_y, int(26 * HAND_SCALE), 10, tick * 0.6, METAL_MID, METAL_LIGHT)

    # panel grooves
    for i in range(5):
        t = (i + 1) / 6
        gy = int(wrist_y + t * (bottom_y - wrist_y))
        w_at = w_top + (w_bot - w_top) * t
        pygame.draw.line(surface, CYAN_DIM,
                         (int(cx - w_at * 0.82), gy),
                         (int(cx + w_at * 0.82), gy), 1)

    # vertical circuit filaments
    for off in [-18, -6, 6, 18]:
        pygame.draw.line(surface, CYAN_GLOW_COL,
                         (cx + off, wrist_y + 12),
                         (cx + off, bottom_y - 12), 1)

    # border
    pygame.draw.polygon(surface, CYAN_MID, pts, 2)

    # wrist connection joint
    _draw_joint(surface, (cx, wrist_y), 20, glow=True)

    # Rotating wrist indicator ring
    ring_r = 26
    for i in range(16):
        a = math.radians(i * 22.5 + tick * 0.8)
        r1, r2 = ring_r - 2, ring_r + 2
        x1 = cx + int(r1 * math.cos(a))
        y1 = wrist_y + int(r1 * math.sin(a))
        x2 = cx + int(r2 * math.cos(a))
        y2 = wrist_y + int(r2 * math.sin(a))
        col = CYAN_DIM if i % 2 else CYAN_MID
        pygame.draw.line(surface, col, (x1, y1), (x2, y2), 1)


def _draw_palm(surface, cx, cy, rotation, tick):
    """Symmetrical armored palm plate with Arc Reactor core."""
    base_pts = [
        (-55, -45), (-22, -60), (22, -60), (55, -45),
        (65,  12),  (45,  55), (-45,  55), (-65,  12),
    ]
    scaled = [(int(p[0] * HAND_SCALE), int(p[1] * HAND_SCALE))
              for p in base_pts]
    rotated = [rotate_point((cx + dx, cy + dy), -rotation, (cx, cy))
               for dx, dy in scaled]

    # shadow
    shadow = [(x + 4, y + 4) for x, y in rotated]
    pygame.draw.polygon(surface, METAL_SHADOW, shadow)

    # dark chassis
    pygame.draw.polygon(surface, METAL_DARK, rotated)

    # inner metallic surface
    cxa = sum(x for x, _ in rotated) / len(rotated)
    cya = sum(y for _, y in rotated) / len(rotated)
    inner = [(int(cxa + (x - cxa) * 0.88),
              int(cya + (y - cya) * 0.88)) for x, y in rotated]
    pygame.draw.polygon(surface, METAL_BASE, inner)

    # highlight on upper edges
    half = len(rotated) // 2
    for i in range(half):
        pygame.draw.line(surface, METAL_HIGHLIGHT,
                         rotated[i], rotated[(i + 1) % len(rotated)], 1)

    # circuit traces palm-centre -> finger anchors
    for f_name, offset in FINGER_ANCHORS.items():
        off_x = -offset[0] if _flipped else offset[0]
        end = rotate_point(
            (cx + off_x * HAND_SCALE, cy + offset[1] * HAND_SCALE),
            rotation, (cx, cy))
        pygame.draw.line(surface, CYAN_GLOW_COL, (cx, cy), end, 1)

    # border
    pygame.draw.polygon(surface, CYAN, rotated, 2)

    # ─── ARC REACTOR CORE ───
    _draw_reactor(surface, cx, cy, tick)


def _draw_reactor(surface, cx, cy, tick):
    """Pulsing Victorian Boiler Core with clockwork and amber steam tubes."""
    pulse = 0.85 + 0.15 * math.sin(tick * 0.06)
    r_outer = int(26 * HAND_SCALE)

    # glow bloom
    g = _get_glow(int(r_outer * pulse), CYAN)
    gw, gh = g.get_size()
    surface.blit(g, (cx - gw // 2, cy - gh // 2),
                 special_flags=pygame.BLEND_ADD)

    # containment ring
    pygame.draw.circle(surface, METAL_DARK, (cx, cy), r_outer + 4)
    pygame.draw.circle(surface, METAL_LIGHT, (cx, cy), r_outer + 4, 2)

    # Rotating Brass clockwork gear in the core
    _draw_gear(surface, cx, cy, int(16 * HAND_SCALE), 8, tick * 1.2, METAL_MID, METAL_HIGHLIGHT)

    # Inner glowing boiler pressure core
    r_inner = int(10 * HAND_SCALE)
    pygame.draw.circle(surface, CYAN_DIM, (cx, cy), r_inner)
    pygame.draw.circle(surface, CYAN, (cx, cy), int(7 * HAND_SCALE))
    pygame.draw.circle(surface, WHITE, (cx, cy), int(3 * HAND_SCALE))


def _draw_finger(surface, anchor, base_angle, wrist_rot, spread,
                 segments, curl, tick):
    """Fully articulated robotic finger with natural 3D inward folding and foreshortening."""
    JOINT_WEIGHTS = [0.50, 0.35, 0.15]
    MAX_BEND = 130  # Symmetrical full curl range

    x, y = anchor
    angle = base_angle + wrist_rot + spread
    joints = [(x, y)]

    # All fingers in a normal hand curl in the same direction (clockwise)
    # to fold down together into the palm as a natural fist.
    bend_direction = -1.0

    for i, seg_len in enumerate(segments):
        # 3D perspective foreshortening: length shrinks as the segment curls into Z-plane
        scale_factor = 1.0 - (curl * 0.50 * (i + 1) / 3.0)
        sx = seg_len * HAND_SCALE * scale_factor

        # Curl curving: accumulate joint bend
        angle += bend_direction * curl * JOINT_WEIGHTS[i] * MAX_BEND
        rad = math.radians(angle)
        
        x2 = x + sx * math.cos(rad)
        y2 = y - sx * math.sin(rad)

        w1, w2 = SEGMENT_WIDTHS[i]
        _draw_3d_segment(surface, (int(x), int(y)),
                         (int(x2), int(y2)), w1, w2)

        joints.append((int(x2), int(y2)))
        x, y = x2, y2

    # pivot joints (decreasing size)
    for i, pos in enumerate(joints):
        _draw_joint(surface, pos, JOINT_RADII[i], glow=(i > 0))

    # colour-coded fingertip sensor
    tip_c = GREEN if curl < 0.33 else (ORANGE if curl < 0.66 else RED)
    _draw_fingertip(surface, (int(x), int(y)), tip_c, tick)


# ═══════════════════════════════════════════════════════════════
#  BACKGROUND + HUD
# ═══════════════════════════════════════════════════════════════

def _draw_background(surface, tick):
    """Dark holographic grid with a sweeping scanner line."""
    surface.fill(BG)

    main_bottom = WIN_H - 150

    # grid
    for gx in range(0, WIN_W, 40):
        pygame.draw.line(surface, GRID, (gx, 55), (gx, main_bottom), 1)
    for gy in range(55, main_bottom, 40):
        pygame.draw.line(surface, GRID, (0, gy), (WIN_W, gy), 1)

    # scanner sweep
    scan_y = 55 + (tick // 4) % (main_bottom - 55)
    pygame.draw.line(surface, CYAN_DIM, (0, scan_y), (WIN_W, scan_y), 1)
    glow_strip = pygame.Surface((WIN_W, 10), pygame.SRCALPHA)
    pygame.draw.rect(glow_strip, (0, 210, 255, 12), (0, 0, WIN_W, 10))
    surface.blit(glow_strip, (0, scan_y - 5))


def _draw_header(surface, font_lg, font_md, mode):
    """Top header bar with system mode indicator."""
    pygame.draw.rect(surface, PANEL, (0, 0, WIN_W, 52))
    pygame.draw.line(surface, CYAN, (0, 52), (WIN_W, 52), 2)

    surface.blit(
        font_lg.render("INMOOV CYBERNETIC ARM // TELEMETRY HUD",
                       True, CYAN), (20, 14))

    mc = GREEN if mode == "LIVE" else ORANGE
    bg_col = (mc[0] // 6, mc[1] // 6, mc[2] // 6)
    pygame.draw.rect(surface, bg_col,
                     (WIN_W - 180, 10, 160, 32), border_radius=5)
    pygame.draw.rect(surface, mc,
                     (WIN_W - 180, 10, 160, 32), width=1, border_radius=5)
    surface.blit(font_md.render(f"SYSTEM: {mode}", True, mc),
                 (WIN_W - 160, 17))


def _draw_telemetry(surface, angles, font_md, font_sm, mode, tick):
    """Left-side diagnostic panel with per-finger telemetry."""
    px, py = 14, 66
    pw, ph = 260, 280

    # translucent panel
    panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.rect(panel, (8, 12, 20, 215), (0, 0, pw, ph),
                     border_radius=6)
    surface.blit(panel, (px, py))
    pygame.draw.rect(surface, CYAN_DIM,
                     (px, py, pw, ph), width=1, border_radius=6)

    # corner brackets
    bk = 20
    for sx, sy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        corner_x = px + sx * pw
        corner_y = py + sy * ph
        dx = 1 if sx == 0 else -1
        dy = 1 if sy == 0 else -1
        pygame.draw.line(surface, CYAN,
                         (corner_x, corner_y),
                         (corner_x + dx * bk, corner_y), 2)
        pygame.draw.line(surface, CYAN,
                         (corner_x, corner_y),
                         (corner_x, corner_y + dy * bk), 2)

    # title
    yo = py + 14
    surface.blit(font_md.render(">> REAL-TIME DIAGNOSTIC", True, TEXT),
                 (px + 16, yo))

    # status lines
    yo += 28
    surface.blit(font_sm.render("  NEURAL BRIDGE  : ACTIVE", True, GREEN),
                 (px + 10, yo))
    yo += 17
    tc = GREEN if mode == "LIVE" else ORANGE
    tt = "LIVE" if mode == "LIVE" else "STANDBY"
    surface.blit(font_sm.render(f"  WEBCAM TRACK   : {tt}", True, tc),
                 (px + 10, yo))
    yo += 17
    surface.blit(font_sm.render("  SYNC QUALITY   : 98.4%", True, TEXT_DIM),
                 (px + 10, yo))
    yo += 17
    surface.blit(font_sm.render("  LATENCY        : <16 ms", True, TEXT_DIM),
                 (px + 10, yo))

    # separator
    yo += 24
    pygame.draw.line(surface, CYAN_DIM,
                     (px + 16, yo), (px + pw - 16, yo), 1)
    yo += 12

    # per-finger servo readouts
    bar_w = 50
    for fn in FINGER_ORDER:
        ca = angles[fn]
        cfg = SERVO_CONFIG[fn]
        frac = max(0.0, min(1.0,
                   (ca - cfg["min"]) / max(cfg["max"] - cfg["min"], 1)))

        surface.blit(
            font_sm.render(f"  {fn.upper():<7}: {ca:>6.1f} deg", True, CYAN),
            (px + 10, yo))

        bx = px + pw - bar_w - 18
        pygame.draw.rect(surface, METAL_DARK,
                         (bx, yo + 3, bar_w, 7), border_radius=3)
        pygame.draw.rect(surface, CYAN,
                         (bx, yo + 3, int(frac * bar_w), 7),
                         border_radius=3)
        yo += 19

    # wrist readout
    yo += 4
    wa = angles["Wrist"]
    surface.blit(
        font_sm.render(f"  WRIST  : {wa:>6.1f} deg", True, MAGENTA),
        (px + 10, yo))


def _draw_bottom_panel(surface, sliders, angles, font_sm):
    """Bottom control strip with manual override sliders."""
    panel_y = WIN_H - 150
    pygame.draw.rect(surface, PANEL, (0, panel_y, WIN_W, 150))
    pygame.draw.line(surface, CYAN, (0, panel_y), (WIN_W, panel_y), 2)

    surface.blit(
        font_sm.render("MANUAL CYBERNETIC CALIBRATION OVERRIDE",
                       True, TEXT_DIM), (20, panel_y + 8))

    for s in sliders.values():
        s.draw(surface, font_sm, angles[s.name])


# ═══════════════════════════════════════════════════════════════
#  SLIDER WIDGET
# ═══════════════════════════════════════════════════════════════

class Slider:
    def __init__(self, x, y, w, name):
        self.rect = pygame.Rect(x, y, w, 10)
        self.name = name
        self.dragging = False

    def _cfg(self):
        if "_Spread" in self.name:
            return {"min": -30, "max": 30}
        return SERVO_CONFIG[self.name]

    def draw(self, surface, font_sm, current_angle):
        cfg = self._cfg()
        frac = (current_angle - cfg["min"]) / max(cfg["max"] - cfg["min"], 1)
        frac = max(0.0, min(1.0, frac))
        knob_x = int(self.rect.x + frac * self.rect.w)

        # track
        pygame.draw.rect(surface, METAL_DARK, self.rect, border_radius=5)
        fill = pygame.Rect(self.rect.x, self.rect.y,
                           int(frac * self.rect.w), self.rect.h)
        pygame.draw.rect(surface, CYAN, fill, border_radius=5)

        # knob
        pygame.draw.circle(surface, CYAN_MID,
                           (knob_x, self.rect.centery), 9)
        pygame.draw.circle(surface, WHITE,
                           (knob_x, self.rect.centery), 5)

        # label
        lbl = font_sm.render(
            f"{self.name.upper()}: {current_angle:.1f}", True, TEXT)
        surface.blit(lbl, (self.rect.x, self.rect.y - 16))

    def handle_event(self, event):
        cfg = self._cfg()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.inflate(0, 20).collidepoint(event.pos):
                self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            frac = (event.pos[0] - self.rect.x) / self.rect.w
            frac = max(0.0, min(1.0, frac))
            return cfg["min"] + frac * (cfg["max"] - cfg["min"])
        return None


# ═══════════════════════════════════════════════════════════════
#  MAIN RENDER LOOP
# ═══════════════════════════════════════════════════════════════

def _run_pygame():
    global _mode, _servo_angles, _flipped

    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption(
        "InMoov Cybernetic Arm // Visual Portfolio Simulator")
    clock = pygame.time.Clock()

    font_lg = pygame.font.SysFont("consolas", 22, bold=True)
    font_md = pygame.font.SysFont("consolas", 15, bold=True)
    font_sm = pygame.font.SysFont("consolas", 12)

    # Build sliders for all controllable components
    components = (FINGER_ORDER + ["Wrist"]
                  + [f"{f}_Spread" for f in FINGER_ORDER])
    sliders = {}
    for i, name in enumerate(components):
        row = i // 6
        col = i % 6
        gap = WIN_W // 7
        sliders[name] = Slider(
            gap * (col + 1) - 60, WIN_H - 108 + row * 42, 105, name)

    tick = 0

    while True:
        clock.tick(FPS)
        tick += 1

        # ── events ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    _mode = "MANUAL" if _mode == "LIVE" else "LIVE"
                if event.key == pygame.K_f:
                    with _lock:
                        _flipped = not _flipped
                    print(f"[HUD] Hand rendering flipped! Mirrored: {_flipped}")
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

            if _mode == "MANUAL":
                for name, slider in sliders.items():
                    res = slider.handle_event(event)
                    if res is not None:
                        with _lock:
                            _servo_angles[name] = res

        # snapshot angles
        with _lock:
            angles = dict(_servo_angles)

        # Center position for 0-300 range is 150 (perfectly straight up)
        wrist_rot = angles["Wrist"] - 150

        # ══════════════ RENDER PIPELINE ══════════════

        # 1) Background grid + scanner
        _draw_background(screen, tick)

        # 2) Forearm (stationary, behind everything else)
        _draw_forearm(screen, ARM_CX, ARM_CY, tick)

        # 3) Palm plate (rotates with wrist)
        palm_rot = wrist_rot if _flipped else -wrist_rot
        _draw_palm(screen, ARM_CX, ARM_CY, palm_rot, tick)

        # 4) Fingers (rotate with palm, curl individually)
        for fname in FINGER_ORDER:
            curl   = servo_to_curl(angles[fname], fname)
            spread = angles.get(f"{fname}_Spread", 0.0)

            if _flipped:
                # Mirror finger anchor X offset
                anch_off = (-FINGER_ANCHORS[fname][0] * HAND_SCALE,
                            FINGER_ANCHORS[fname][1] * HAND_SCALE)
                # Mirror finger base angle (symmetrical around 90)
                base_ang = 180 - FINGER_BASE_ANGLES[fname]
                w_rot_draw = wrist_rot
                spr_draw = -spread
            else:
                anch_off = (FINGER_ANCHORS[fname][0] * HAND_SCALE,
                            FINGER_ANCHORS[fname][1] * HAND_SCALE)
                base_ang = FINGER_BASE_ANGLES[fname]
                w_rot_draw = -wrist_rot
                spr_draw = spread

            raw_anch = (ARM_CX + anch_off[0], ARM_CY + anch_off[1])
            rot_anch = rotate_point(raw_anch, w_rot_draw,
                                    (ARM_CX, ARM_CY))

            _draw_finger(screen, rot_anch,
                         base_ang,
                         w_rot_draw, spr_draw,
                         FINGER_SEGMENTS[fname], curl, tick)

        # 5) HUD overlays (drawn last, on top)
        _draw_header(screen, font_lg, font_md, _mode)
        _draw_telemetry(screen, angles, font_md, font_sm, _mode, tick)
        _draw_bottom_panel(screen, sliders, angles, font_sm)

        pygame.display.flip()


# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    _run_pygame()
