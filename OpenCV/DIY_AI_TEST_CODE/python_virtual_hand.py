import pygame
import sys
import math
import threading

# ─────────────────────────────────────────────
#  CONFIGURATION  —  match your physical servo tuning
# ─────────────────────────────────────────────

SERVO_CONFIG = {
    "Thumb":  {"min": 20, "max": 150},
    "Index":  {"min": 20, "max": 160},
    "Middle": {"min": 20, "max": 160},
    "Ring":   {"min": 25, "max": 155},
    "Pinky":  {"min": 25, "max": 145},
    "Wrist":  {"min": 0,  "max": 180}, # Rotation axis
}

FINGER_ORDER = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

# ─────────────────────────────────────────────
#  COLOURS
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

# ═══════════════════════════════════════════════════════════
# 🎯 HAND ALIGNMENT TUNING (Adjust to match your camera view)
# ═══════════════════════════════════════════════════════════
PALM_CENTER_X = 450   # ⬅️ Horizontal center of virtual hand (0-900)
PALM_CENTER_Y = 310   # ⬇️ Vertical center of virtual hand (0-680)
HAND_SCALE    = 1.0   # 🔍 Zoom: 0.8=smaller, 1.0=normal, 1.2=larger
MIRROR_HAND   = False # 🔄 Set True if left/right appear flipped
# ═══════════════════════════════════════════════════════════

# ─────────────────────────────────────────────
#  GEOMETRY
# ─────────────────────────────────────────────
FINGER_SEGMENTS = {
    "Thumb":  [38, 28, 22],
    "Index":  [52, 38, 26],
    "Middle": [56, 40, 28],
    "Ring":   [50, 36, 26],
    "Pinky":  [40, 28, 20],
}

PALM_W, PALM_H = 130, 110
FINGER_ANCHORS = {
    "Thumb":  (-62,  30),
    "Index":  (-42, -55),
    "Middle": (-12, -62),
    "Ring":   ( 20, -58),
    "Pinky":  ( 52, -48),
}

FINGER_BASE_ANGLES = {
    "Thumb":  145,
    "Index":  100,
    "Middle":  95,
    "Ring":    90,
    "Pinky":   82,
}

# ─────────────────────────────────────────────
#  SHARED STATE
# ─────────────────────────────────────────────
_lock          = threading.Lock()
# Initialize standard servos + virtual spread axes for cartoonish movement
_servo_angles  = {f: SERVO_CONFIG[f]["min"] for f in SERVO_CONFIG}
_servo_angles.update({f"{f}_Spread": 0.0 for f in FINGER_ORDER}) 
_mode          = "MANUAL"

def send_to_virtual_hand(servo_commands: dict):
    global _mode
    with _lock:
        for component, angle in servo_commands.items():
            if component in _servo_angles:
                _servo_angles[component] = float(angle)
        _mode = "LIVE"

def init_virtual_hand():
    t = threading.Thread(target=_run_pygame, daemon=True)
    t.start()
    return t

# ─────────────────────────────────────────────
#  MATHS HELPERS
# ─────────────────────────────────────────────

def rotate_point(point, angle_deg, center):
    """Rotates a point (x, y) around a center by angle_deg."""
    angle_rad = math.radians(angle_deg)
    px, py = point
    cx, cy = center
    qx = cx + math.cos(angle_rad) * (px - cx) - math.sin(angle_rad) * (py - cy)
    qy = cy + math.sin(angle_rad) * (px - cx) + math.cos(angle_rad) * (py - cy)
    return int(qx), int(qy)

def servo_to_curl(angle, finger_name):
    cfg   = SERVO_CONFIG[finger_name]
    frac  = (angle - cfg["min"]) / max(cfg["max"] - cfg["min"], 1)
    return max(0.0, min(1.0, frac))

def draw_finger(surface, anchor, base_angle_deg, wrist_rot, spread,
                segments, curl, center):
    JOINT_WEIGHTS = [0.50, 0.35, 0.15]
    MAX_TOTAL_BEND = 240
    
    # Initial rotated anchor
    x, y = anchor
    # Base angle is affected by wrist rotation AND virtual spread (side-to-side)
    angle = base_angle_deg + wrist_rot + spread
    
    joint_positions = [(x, y)]

    for i, seg_len in enumerate(segments):
        angle -= curl * JOINT_WEIGHTS[i] * MAX_TOTAL_BEND
        rad   = math.radians(angle)
        x2    = x + seg_len * math.cos(rad)
        y2    = y - seg_len * math.sin(rad)
        
        thickness = max(3, 7 - i * 2)
        pygame.draw.line(surface, BONE_COL, (x, y), (int(x2), int(y2)), thickness)

        joint_positions.append((int(x2), int(y2)))
        x, y = x2, y2

    for i, pos in enumerate(joint_positions):
        r = [8, 6, 5, 4][i]
        pygame.draw.circle(surface, JOINT_COL, pos, r)
    
    tip_c = GREEN if curl < 0.33 else (ORANGE if curl < 0.66 else RED)
    pygame.draw.circle(surface, tip_c, (int(x), int(y)), 6)

def draw_palm(surface, cx, cy, rotation):
    # Create a surface for the palm to rotate it easily
    palm_surf = pygame.Surface((PALM_W + 40, PALM_H + 60), pygame.SRCALPHA)
    rect = pygame.Rect(20, 20, PALM_W, PALM_H)
    pygame.draw.rect(palm_surf, PALM_COL, rect, border_radius=18)
    pygame.draw.rect(palm_surf, BONE_COL, rect, width=2, border_radius=18)
    # Wrist bump
    pygame.draw.ellipse(palm_surf, PALM_COL, (20 + PALM_W//2 - 35, 20 + PALM_H - 10, 70, 30))
    
    rotated_palm = pygame.transform.rotate(palm_surf, rotation)
    new_rect = rotated_palm.get_rect(center=(cx, cy))
    surface.blit(rotated_palm, new_rect.topleft)

# ─────────────────────────────────────────────
#  WIDGETS
# ─────────────────────────────────────────────

class Slider:
    def __init__(self, x, y, w, name):
        self.rect  = pygame.Rect(x, y, w, 14)
        self.name  = name
        self.dragging = False

    def draw(self, surface, font_sm, current_angle):
        # Handle regular servos vs Spread (virtual)
        if "_Spread" in self.name:
            cfg = {"min": -30, "max": 30}
        else:
            cfg = SERVO_CONFIG[self.name]
            
        frac  = (current_angle - cfg["min"]) / max(cfg["max"] - cfg["min"], 1)
        frac  = max(0.0, min(1.0, frac))
        knob_x = int(self.rect.x + frac * self.rect.w)
        pygame.draw.rect(surface, SLIDER_BG, self.rect, border_radius=7)
        fill = pygame.Rect(self.rect.x, self.rect.y, int(frac * self.rect.w), self.rect.h)
        pygame.draw.rect(surface, SLIDER_FG, fill, border_radius=7)
        pygame.draw.circle(surface, (255,255,255), (knob_x, self.rect.centery), 10)
        lbl = font_sm.render(f"{self.name}: {current_angle:.1f}", True, TEXT_COL)
        surface.blit(lbl, (self.rect.x, self.rect.y - 18))

    def handle_event(self, event):
        if "_Spread" in self.name:
            cfg = {"min": -30, "max": 30}
        else:
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
#  MAIN LOOP
# ─────────────────────────────────────────────

def _run_pygame():
    global _mode, _servo_angles
    pygame.init()
    pygame.font.init()  # ⚡ Explicitly init font subsystem for threaded safety
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("InMoov Virtual Hand - Visual Portfolio")
    clock = pygame.time.Clock()
    font_lg = pygame.font.SysFont("consolas", 22, bold=True)
    font_md = pygame.font.SysFont("consolas", 16)
    font_sm = pygame.font.SysFont("consolas", 13)

    # Use tunable palm center coordinates
    PALM_CX, PALM_CY = PALM_CENTER_X, PALM_CENTER_Y
    
    # Sliders for ALL components including Wrist and Spreads
    components = FINGER_ORDER + ["Wrist"] + [f"{f}_Spread" for f in FINGER_ORDER]
    sliders = {}
    
    # Arrange sliders in rows for better space management
    for i, name in enumerate(components):
        row = i // 6
        col = i % 6
        gap = WIN_W // 7
        sliders[name] = Slider(gap * (col + 1) - 60, WIN_H - 120 + (row * 40), 100, name)

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m: _mode = "MANUAL" if _mode == "LIVE" else "LIVE"
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
            
            if _mode == "MANUAL":
                for name, slider in sliders.items():
                    res = slider.handle_event(event)
                    if res is not None:
                        with _lock: _servo_angles[name] = res

        with _lock: angles = dict(_servo_angles)
        
        screen.fill(BG)
        
        # UI
        pygame.draw.rect(screen, PANEL_BG, (0, 0, WIN_W, 52))
        screen.blit(font_lg.render("InMoov Virtual Portfolio - Hand Simulator", True, ACCENT), (20, 14))
        mode_col = GREEN if _mode == "LIVE" else ORANGE
        screen.blit(font_md.render(f"MODE: {_mode}", True, mode_col), (WIN_W - 150, 17))
        
        pygame.draw.rect(screen, PANEL_BG, (0, WIN_H - 145, WIN_W, 145))
        for s in sliders.values(): s.draw(screen, font_sm, angles[s.name])

        # Rotation Logic
        wrist_rot = angles["Wrist"] - 90 
        
        # Draw Palm (with optional mirroring for camera alignment)
        display_cx = PALM_CX if not MIRROR_HAND else (WIN_W - PALM_CX)
        draw_palm(screen, display_cx, PALM_CY, wrist_rot)
        
        # Draw Fingers with rotation and spread
        for name in FINGER_ORDER:
            curl = servo_to_curl(angles[name], name)
            spread = angles.get(f"{name}_Spread", 0.0)
            
            # Apply scale to anchor offsets for size tuning
            anchor_offset = (FINGER_ANCHORS[name][0] * HAND_SCALE, FINGER_ANCHORS[name][1] * HAND_SCALE)
            orig_anchor = (PALM_CX + anchor_offset[0], PALM_CY + anchor_offset[1])
            rot_anchor = rotate_point(orig_anchor, -wrist_rot, (PALM_CX, PALM_CY))
            
            draw_finger(screen, rot_anchor, FINGER_BASE_ANGLES[name], -wrist_rot, spread,
                        FINGER_SEGMENTS[name], curl, (PALM_CX, PALM_CY))

        pygame.display.flip()
        # ⚡ Small wait helps sync with main thread and reduces CPU usage
        pygame.time.wait(1)

if __name__ == "__main__":
    _run_pygame()
