"""
virtual_hand.py
===============
A pygame simulator that draws a 2D robotic hand and animates
each finger based on the servo angles coming from STATICMODE.py.

HOW TO USE:
-----------
1.  Install pygame:   pip install pygame
2.  Put this file in the SAME folder as STATICMODE.py
3.  In STATICMODE.py, replace the print line:
        print(f'TRACKING: {servo_commands}', end='\r')
    with:
        send_to_virtual_hand(servo_commands)
4.  Import this at the top of STATICMODE.py:
        from virtual_hand import VirtualHand, send_to_virtual_hand, init_virtual_hand

5.  Add these three lines near the top of STATICMODE.py (after imports):
        virtual_hand = init_virtual_hand()

6.  Run STATICMODE.py as normal. The pygame window opens automatically.

CONTROLS (in the pygame window):
---------------------------------
  Sliders at bottom  →  manually drag each finger for testing WITHOUT webcam
  LIVE mode          →  servo angles come from your real hand via camera
  ESC                →  close simulator
"""

import pygame
import sys
import math
import threading

# ─────────────────────────────────────────────
#  CONFIGURATION  —  edit these to match your servo tuning
# ─────────────────────────────────────────────

SERVO_CONFIG = {
    "Thumb":  {"min": 20, "max": 150},
    "Index":  {"min": 20, "max": 160},
    "Middle": {"min": 20, "max": 160},
    "Ring":   {"min": 25, "max": 155},
    "Pinky":  {"min": 25, "max": 145},
}

FINGER_ORDER = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

# ─────────────────────────────────────────────
#  COLOURS  (R, G, B)
# ─────────────────────────────────────────────
BG          = (15,  15,  25)
PANEL_BG    = (25,  25,  40)
PALM_COL    = (60,  60,  90)
BONE_COL    = (180, 190, 220)
JOINT_COL   = (255, 255, 255)
TIP_COL     = (80,  200, 140)
TEXT_COL    = (200, 210, 230)
ACCENT      = (80,  140, 255)
SLIDER_BG   = (40,  40,  60)
SLIDER_FG   = (80,  140, 255)
LABEL_COL   = (140, 150, 180)
GREEN       = (80,  200, 140)
ORANGE      = (255, 160,  60)
RED         = (255,  80,  80)

# ─────────────────────────────────────────────
#  WINDOW
# ─────────────────────────────────────────────
WIN_W, WIN_H = 900, 680
FPS          = 30

# ─────────────────────────────────────────────
#  FINGER GEOMETRY  (all measurements in pixels)
# ─────────────────────────────────────────────
# Each finger has 3 bone segments: proximal, middle, distal
# The angle stored in servo_angles drives how much each finger curls.
# We map the servo angle to a "curl angle" for the finger drawing.

FINGER_SEGMENTS = {
    #         proximal  middle  distal
    "Thumb":  [38,      28,     22],
    "Index":  [52,      38,     26],
    "Middle": [56,      40,     28],
    "Ring":   [50,      36,     26],
    "Pinky":  [40,      28,     20],
}

# Palm anchor points (where each finger attaches to the palm)
# These are relative to the palm centre drawn on screen
PALM_W, PALM_H = 130, 110
FINGER_ANCHORS = {
    "Thumb":  (-62,  30),   # thumb sticks out to the side
    "Index":  (-42, -55),
    "Middle": (-12, -62),
    "Ring":   ( 20, -58),
    "Pinky":  ( 52, -48),
}

# Base angle each finger points in (degrees, 0=right, 90=up)
FINGER_BASE_ANGLES = {
    "Thumb":  145,   # points up-left
    "Index":  100,
    "Middle":  95,
    "Ring":    90,
    "Pinky":   82,
}


# ─────────────────────────────────────────────
#  SHARED STATE  (thread-safe via lock)
# ─────────────────────────────────────────────
_lock          = threading.Lock()
_servo_angles  = {f: SERVO_CONFIG[f]["min"] for f in FINGER_ORDER}   # start fully closed
_mode          = "MANUAL"    # "MANUAL" or "LIVE"


def send_to_virtual_hand(servo_commands: dict):
    """
    Call this from STATICMODE.py instead of printing.
    servo_commands = {"Thumb": 90.0, "Index": 120.5, ...}
    """
    global _mode
    with _lock:
        for finger, angle in servo_commands.items():
            if finger in _servo_angles:
                _servo_angles[finger] = float(angle)
        _mode = "LIVE"


def init_virtual_hand():
    """Call once at the start of STATICMODE.py to launch the pygame window."""
    t = threading.Thread(target=_run_pygame, daemon=True)
    t.start()
    return t


# ─────────────────────────────────────────────
#  MATHS HELPERS
# ─────────────────────────────────────────────

def servo_to_curl(angle, finger_name):
    """
    Converts a servo angle (e.g. 20–160°) to a curl fraction (0.0–1.0).
    0.0 = fully open, 1.0 = fully closed.
    """
    cfg   = SERVO_CONFIG[finger_name]
    frac  = (angle - cfg["min"]) / max(cfg["max"] - cfg["min"], 1)
    return max(0.0, min(1.0, frac))


def draw_finger(surface, anchor_x, anchor_y, base_angle_deg,
                segments, curl, colour_bone, colour_joint, colour_tip):
    """
    Draws a finger made of 3 bone segments starting from (anchor_x, anchor_y).

    anchor_x/y  : where the finger attaches to the palm
    base_angle  : direction the finger initially points (degrees, pygame convention)
    segments    : list of 3 pixel lengths [proximal, middle, distal]
    curl        : 0.0 (straight) → 1.0 (fully curled)

    FIX: Each joint now bends BEFORE its segment is drawn, so all 3 joints
    (including the base knuckle) contribute to the curl animation.

    JOINT BEND WEIGHTS — how much each joint contributes to the total curl.
    Real fingers don't bend all joints equally:
      - MCP (base knuckle)  : bends the most  → weight 0.5  (50% of curl)
      - PIP (middle joint)  : bends a lot     → weight 0.35 (35% of curl)
      - DIP (tip joint)     : bends a little  → weight 0.15 (15% of curl)
    These must add up to 1.0.
    """
    # ── CHANGED: per-joint bend weights (must sum to 1.0) ──────────────────
    JOINT_WEIGHTS = [0.50, 0.35, 0.15]   # MCP, PIP, DIP
    MAX_TOTAL_BEND = 240   # total degrees of bend across all 3 joints at curl=1.0
    # ───────────────────────────────────────────────────────────────────────

    x, y  = float(anchor_x), float(anchor_y)
    angle = base_angle_deg   # current running angle (starts straight)

    joint_positions = [(int(x), int(y))]

    for i, seg_len in enumerate(segments):

        # ── CHANGED: bend THIS joint BEFORE drawing its segment ────────────
        # Old code subtracted the bend AFTER drawing, so joint 0 never bent.
        # Now we subtract FIRST so every joint (including the base) bends.
        angle -= curl * JOINT_WEIGHTS[i] * MAX_TOTAL_BEND
        # ───────────────────────────────────────────────────────────────────

        rad   = math.radians(angle)
        x2    = x + seg_len * math.cos(rad)
        y2    = y - seg_len * math.sin(rad)   # pygame y is flipped

        # ── CHANGED: bone thickness tapers toward the tip (more realistic) ─
        thickness = max(3, 7 - i * 2)   # proximal=7, middle=5, distal=3
        # ───────────────────────────────────────────────────────────────────
        pygame.draw.line(surface, colour_bone,
                         (int(x), int(y)), (int(x2), int(y2)), thickness)

        joint_positions.append((int(x2), int(y2)))
        x, y = x2, y2

    # Draw joints — ── CHANGED: size also tapers toward tip ─────────────────
    for i, pos in enumerate(joint_positions):
        r = [8, 6, 5, 4][i]   # base knuckle biggest, tip smallest
        pygame.draw.circle(surface, colour_joint, pos, r)
    # ─────────────────────────────────────────────────────────────────────────

    # Draw fingertip
    pygame.draw.circle(surface, colour_tip, (int(x), int(y)), 6)


def draw_palm(surface, cx, cy):
    """Draws the palm rectangle centred at (cx, cy)."""
    rect = pygame.Rect(cx - PALM_W//2, cy - PALM_H//2, PALM_W, PALM_H)
    pygame.draw.rect(surface, PALM_COL, rect, border_radius=18)
    pygame.draw.rect(surface, BONE_COL, rect, width=2, border_radius=18)
    # Wrist bump
    pygame.draw.ellipse(surface, PALM_COL,
                        (cx - 35, cy + PALM_H//2 - 10, 70, 30))


# ─────────────────────────────────────────────
#  SLIDER WIDGET
# ─────────────────────────────────────────────

class Slider:
    def __init__(self, x, y, w, finger_name):
        self.rect  = pygame.Rect(x, y, w, 14)
        self.name  = finger_name
        self.dragging = False

    def draw(self, surface, font_sm, current_angle):
        cfg   = SERVO_CONFIG[self.name]
        frac  = (current_angle - cfg["min"]) / max(cfg["max"] - cfg["min"], 1)
        frac  = max(0.0, min(1.0, frac))
        knob_x = int(self.rect.x + frac * self.rect.w)

        # Track
        pygame.draw.rect(surface, SLIDER_BG, self.rect, border_radius=7)
        # Fill
        fill = pygame.Rect(self.rect.x, self.rect.y,
                           int(frac * self.rect.w), self.rect.h)
        pygame.draw.rect(surface, SLIDER_FG, fill, border_radius=7)
        # Knob
        pygame.draw.circle(surface, (255,255,255),
                           (knob_x, self.rect.centery), 10)

        # Label
        lbl = font_sm.render(f"{self.name}: {current_angle:.1f}°", True, TEXT_COL)
        surface.blit(lbl, (self.rect.x, self.rect.y - 18))

    def handle_event(self, event):
        """Returns new angle if dragged, else None."""
        cfg = SERVO_CONFIG[self.name]
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


# ─────────────────────────────────────────────
#  MAIN PYGAME LOOP
# ─────────────────────────────────────────────

def _run_pygame():
    global _mode, _servo_angles

    pygame.init()
    screen  = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("InMoov Virtual Hand — Simulator")
    clock   = pygame.time.Clock()

    font_lg = pygame.font.SysFont("consolas", 22, bold=True)
    font_md = pygame.font.SysFont("consolas", 16)
    font_sm = pygame.font.SysFont("consolas", 13)

    # Palm centre position on screen
    PALM_CX, PALM_CY = 450, 310

    # Build sliders — one per finger, across the bottom panel
    slider_y  = WIN_H - 80
    gap       = WIN_W // (len(FINGER_ORDER) + 1)
    sliders   = {}
    for i, name in enumerate(FINGER_ORDER):
        sx = gap * (i + 1) - 70
        sliders[name] = Slider(sx, slider_y, 140, name)

    # Local copy of angles for slider use (manual mode)
    manual_angles = {f: SERVO_CONFIG[f]["min"] for f in FINGER_ORDER}

    running = True
    while running:
        clock.tick(FPS)

        # ── Events ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_m:   # toggle manual/live
                    _mode = "MANUAL" if _mode == "LIVE" else "LIVE"

            # Slider dragging only in MANUAL mode
            if _mode == "MANUAL":
                for name, slider in sliders.items():
                    result = slider.handle_event(event)
                    if result is not None:
                        manual_angles[name] = result
                        with _lock:
                            _servo_angles[name] = result

        # ── Get current angles ──
        with _lock:
            display_angles = dict(_servo_angles)

        if _mode == "MANUAL":
            display_angles = dict(manual_angles)

        # ─────────── DRAW ───────────

        screen.fill(BG)

        # ── Top bar ──
        pygame.draw.rect(screen, PANEL_BG, (0, 0, WIN_W, 52))
        title = font_lg.render("InMoov Virtual Hand Simulator", True, ACCENT)
        screen.blit(title, (20, 14))

        mode_col  = GREEN if _mode == "LIVE" else ORANGE
        mode_surf = font_md.render(f"[M] MODE: {_mode}", True, mode_col)
        screen.blit(mode_surf, (WIN_W - 200, 17))

        # ── Bottom panel (sliders) ──
        pygame.draw.rect(screen, PANEL_BG, (0, WIN_H - 115, WIN_W, 115))
        hint = font_sm.render(
            "MANUAL: drag sliders to test fingers   |   LIVE: angles come from your webcam   |   [M] toggle   |   ESC quit",
            True, LABEL_COL)
        screen.blit(hint, (20, WIN_H - 115 + 8))

        for name, slider in sliders.items():
            slider.draw(screen, font_sm, display_angles[name])

        # ── Palm ──
        draw_palm(screen, PALM_CX, PALM_CY)

        # ── Fingers ──
        for name in FINGER_ORDER:
            angle    = display_angles[name]
            curl     = servo_to_curl(angle, name)
            ax, ay   = FINGER_ANCHORS[name]
            base_ang = FINGER_BASE_ANGLES[name]
            segs     = FINGER_SEGMENTS[name]

            # Colour tip based on curl amount
            if curl < 0.33:
                tip_c = GREEN
            elif curl < 0.66:
                tip_c = ORANGE
            else:
                tip_c = RED

            draw_finger(
                screen,
                PALM_CX + ax, PALM_CY + ay,
                base_ang, segs, curl,
                BONE_COL, JOINT_COL, tip_c
            )

        # ── Side panel: live readout ──
        panel_x = 20
        pygame.draw.rect(screen, PANEL_BG,
                         (panel_x - 8, 60, 200, 240), border_radius=10)
        hdr = font_md.render("SERVO ANGLES", True, ACCENT)
        screen.blit(hdr, (panel_x, 70))

        for i, name in enumerate(FINGER_ORDER):
            angle = display_angles[name]
            curl  = servo_to_curl(angle, name)
            col   = GREEN if curl < 0.33 else (ORANGE if curl < 0.66 else RED)
            bar_w = int(curl * 120)
            by    = 100 + i * 40
            # bar background
            pygame.draw.rect(screen, SLIDER_BG, (panel_x, by + 18, 120, 8), border_radius=4)
            # bar fill
            pygame.draw.rect(screen, col, (panel_x, by + 18, bar_w, 8), border_radius=4)
            lbl = font_sm.render(f"{name:<6}  {angle:>6.1f}°", True, TEXT_COL)
            screen.blit(lbl, (panel_x, by))

        # ── Instruction box ──
        ibox_y = 320
        pygame.draw.rect(screen, PANEL_BG,
                         (panel_x - 8, ibox_y, 200, 180), border_radius=10)
        lines = [
            "HOW TO USE:",
            "",
            "1. Run STATICMODE.py",
            "2. Press O → open hand",
            "3. Press C → close hand",
            "4. Press S → lock calibra",
            "5. Hand controls robot!",
            "",
            "Green  = open",
            "Orange = halfway",
            "Red    = closed",
        ]
        for j, line in enumerate(lines):
            c   = ACCENT if j == 0 else LABEL_COL
            txt = font_sm.render(line, True, c)
            screen.blit(txt, (panel_x, ibox_y + 10 + j * 15))

        pygame.display.flip()

    pygame.quit()


# ─────────────────────────────────────────────
#  STANDALONE MODE
#  Run this file directly to test sliders alone
#  without STATICMODE.py or a webcam
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("Running in STANDALONE mode — use sliders to test the hand.")
    print("To connect to your webcam, import this from STATICMODE.py")
    _run_pygame()
