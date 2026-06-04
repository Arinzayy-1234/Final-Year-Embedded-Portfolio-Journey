"""
python_virtual_hand.py  -  InMoov Cybernetic Arm 3D Simulator (Iron Man Edition)
=============================================================================
Renders a stunning 3D Iron Man style cybernetic arm with metallic red/gold shading,
a glowing ice-blue palm repulsor core, animated HUD telemetry, and interactive
mouse-drag camera rotation.

Interface:
    init_virtual_hand()               -> starts the renderer thread
    send_to_virtual_hand(commands)    -> pushes servo angles dict
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import sys
import threading

# ═══════════════════════════════════════════════════════════════
#  SERVO CONFIGURATION  (must match gesture_module.py)
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
#  WINDOW AND LAYOUT CONSTANTS
# ═══════════════════════════════════════════════════════════════

WIN_W, WIN_H = 960, 720
FPS = 60

# ═══════════════════════════════════════════════════════════════
#  PREMIUM DARK HUD COLORS AND MODERN SCI-FI PALETTE
# ═══════════════════════════════════════════════════════════════

BG             = (10, 8, 6)         # Deep charcoal walnut
GRID           = (25, 20, 15)       # Burnished copper grid
PANEL          = (16, 12, 9)        # Dark mahogany inlay
PANEL_BORDER   = (65, 45, 30)       # Aged brass border

# Iron Man Cybernetic Color Theme
RED_METAL      = (0.78, 0.08, 0.10) # Hot-rod cherry red
GOLD_METAL     = (0.88, 0.68, 0.15) # Metallic gold plating
ICE_BLUE       = (0.00, 0.75, 1.00) # Glowing repulsor blue
WHITE          = (225, 255, 235)    # Incandescent warm white
TEXT           = (205, 235, 215)    # Ivory text
TEXT_DIM       = (110, 135, 120)    # Soft mossy dust

# HUD Neon Indicators
CYAN           = ICE_BLUE
CYAN_MID       = (0, 140, 200)
CYAN_DIM       = (0, 70, 110)
CYAN_GLOW_COL  = (0, 35, 60)
MAGENTA        = (230, 40, 90)      # Crimson highlight
GREEN          = (0, 220, 100)      # System active green
ORANGE         = (255, 110, 0)      # System warning/override
RED            = (220, 30, 30)

# ═══════════════════════════════════════════════════════════════
#  ARM GEOMETRY (3D SCALE FACTOR & DIMENSIONS)
# ═══════════════════════════════════════════════════════════════

# Finger segment lengths (3D scaled phalanx bounds)
FINGER_SEGMENTS = {
    "Thumb":  [44, 34, 26],
    "Index":  [60, 44, 32],
    "Middle": [64, 47, 34],
    "Ring":   [58, 42, 32],
    "Pinky":  [47, 34, 24],
}

# Knuckle anchors in 2D space relative to palm center
FINGER_ANCHORS = {
    "Thumb":  ( 60,  20),
    "Index":  ( 42, -54),
    "Middle": ( 14, -60),
    "Ring":   (-14, -60),
    "Pinky":  (-42, -48),
}

# Resting angle for each finger (degrees splay splay)
FINGER_BASE_ANGLES = {
    "Thumb":   40,
    "Index":   78,
    "Middle":  90,
    "Ring":   102,
    "Pinky":  114,
}

SEGMENT_WIDTHS = [
    (14, 11),   # proximal
    (11,  8),   # middle
    ( 8,  5),   # distal
]

JOINT_RADII = [12, 10, 8, 6]

# Palm 3D boundary polygon vertices (scaled relative to (0.0, 0.0))
PALM_VERTS = [
    ( 0.65,  0.15),
    ( 0.50,  0.65),
    ( 0.18,  0.75),
    (-0.18,  0.75),
    (-0.50,  0.65),
    (-0.65,  0.15),
    (-0.50, -0.70),
    ( 0.50, -0.70),
]

# ═══════════════════════════════════════════════════════════════
#  THREAD-SAFE STATE VARIABLES
# ═══════════════════════════════════════════════════════════════

_lock         = threading.Lock()
_servo_angles = {f: SERVO_CONFIG[f]["min"] for f in SERVO_CONFIG}
_servo_angles["Wrist"] = 150.0  # Center position
_servo_angles.update({f"{f}_Spread": 0.0 for f in FINGER_ORDER})
_mode         = "MANUAL"
_flipped      = False  # Mirror toggle

def send_to_virtual_hand(servo_commands: dict):
    """Updates target servo angles thread-safely."""
    global _mode
    with _lock:
        for component, angle in servo_commands.items():
            if component in _servo_angles:
                _servo_angles[component] = float(angle)
        _mode = "LIVE"

def init_virtual_hand():
    """Starts the 3D visual simulator on a daemon thread."""
    t = threading.Thread(target=_run_pygame, daemon=True)
    t.start()
    return t

# ═══════════════════════════════════════════════════════════════
#  OPENGL 3D GEOMETRY GENERATORS
# ═══════════════════════════════════════════════════════════════

def set_material(diffuse, specular=[0.8, 0.8, 0.8], shininess=60.0, emission=[0.0, 0.0, 0.0]):
    """Applies clean lighting characteristics to front & back faces."""
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [*diffuse[:3], 1.0])
    ambient = [c * 0.25 for c in diffuse[:3]]
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [*ambient, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [*specular[:3], 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shininess)
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [*emission[:3], 1.0])

def draw_sphere(radius, slices=12, stacks=12, color=None, emission=None):
    """Draws a procedural 3D sphere with smooth normals."""
    if color:
        set_material(color, specular=[0.9, 0.9, 0.9], shininess=70.0, emission=emission or [0,0,0])
        
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        z0  = math.sin(lat0) * radius
        zr0 = math.cos(lat0) * radius

        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        z1  = math.sin(lat1) * radius
        zr1 = math.cos(lat1) * radius

        glBegin(GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2 * math.pi * float(j) / slices
            x = math.cos(lng)
            y = math.sin(lng)
            
            glNormal3f(x * math.cos(lat1), y * math.cos(lat1), math.sin(lat1))
            glVertex3f(x * zr1, y * zr1, z1)
            
            glNormal3f(x * math.cos(lat0), y * math.cos(lat0), math.sin(lat0))
            glVertex3f(x * zr0, y * zr0, z0)
        glEnd()

def draw_cylinder(r_bottom, r_top, height, slices=12, color=None):
    """Draws a tapered 3D cylinder along the Z-axis."""
    if color:
        set_material(color, specular=[0.8, 0.8, 0.8], shininess=50.0)
        
    glBegin(GL_QUAD_STRIP)
    for i in range(slices + 1):
        angle = 2 * math.pi * float(i) / slices
        c = math.cos(angle)
        s = math.sin(angle)
        
        glNormal3f(c, s, 0.0)
        glVertex3f(c * r_bottom, s * r_bottom, 0.0)
        glVertex3f(c * r_top, s * r_top, height)
    glEnd()

    # Draw end caps to make it solid
    glBegin(GL_TRIANGLE_FAN)
    glNormal3f(0.0, 0.0, -1.0)
    glVertex3f(0.0, 0.0, 0.0)
    for i in range(slices + 1):
        angle = -2 * math.pi * float(i) / slices
        glVertex3f(math.cos(angle) * r_bottom, math.sin(angle) * r_bottom, 0.0)
    glEnd()

    glBegin(GL_TRIANGLE_FAN)
    glNormal3f(0.0, 0.0, 1.0)
    glVertex3f(0.0, 0.0, height)
    for i in range(slices + 1):
        angle = 2 * math.pi * float(i) / slices
        glVertex3f(math.cos(angle) * r_top, math.sin(angle) * r_top, height)
    glEnd()

def draw_extruded_palm(vertices, thickness, color):
    """Draws a 3D extruded flat polygon with side normals."""
    set_material(color, specular=[0.9, 0.5, 0.5], shininess=80.0)

    # Front Face (Z = thickness/2)
    glBegin(GL_POLYGON)
    glNormal3f(0.0, 0.0, 1.0)
    for vx, vy in vertices:
        glVertex3f(vx, vy, thickness / 2.0)
    glEnd()

    # Back Face (Z = -thickness/2)
    glBegin(GL_POLYGON)
    glNormal3f(0.0, 0.0, -1.0)
    for vx, vy in reversed(vertices):
        glVertex3f(vx, vy, -thickness / 2.0)
    glEnd()

    # Perimeter Sides
    glBegin(GL_QUAD_STRIP)
    n_pts = len(vertices)
    for i in range(n_pts + 1):
        idx = i % n_pts
        vx, vy = vertices[idx]
        
        # Side normal calculation
        prev_idx = (idx - 1) % n_pts
        pvx, pvy = vertices[prev_idx]
        dx = vx - pvx
        dy = vy - pvy
        len_edge = math.hypot(dx, dy)
        if len_edge > 0:
            glNormal3f(dy / len_edge, -dx / len_edge, 0.0)
        
        glVertex3f(vx, vy, thickness / 2.0)
        glVertex3f(vx, vy, -thickness / 2.0)
    glEnd()

def draw_ring(inner_r, outer_r, thickness, color):
    """Draws a flat gold containment ring."""
    set_material(color, specular=[1.0, 0.9, 0.4], shininess=100.0)
    slices = 24
    glBegin(GL_QUAD_STRIP)
    for i in range(slices + 1):
        angle = 2 * math.pi * float(i) / slices
        c = math.cos(angle)
        s = math.sin(angle)
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(c * inner_r, s * inner_r, thickness / 2.0)
        glVertex3f(c * outer_r, s * outer_r, thickness / 2.0)
    glEnd()

# ═══════════════════════════════════════════════════════════════
#  GL GLOW & SCENE HELPERS
# ═══════════════════════════════════════════════════════════════

def draw_repulsor_glow(charge_factor):
    """Renders the pulsing Iron Man Repulsor Core with dynamic intensity."""
    t_sec = pygame.time.get_ticks() * 0.001
    
    # Pulse is stronger and faster when charging / wide open
    pulse_speed = 8.0 + 8.0 * charge_factor
    pulse = 0.85 + 0.15 * math.sin(t_sec * pulse_speed)
    
    # Glowing radius responds dynamically to splay
    r = 0.16 + 0.08 * charge_factor + 0.02 * math.sin(t_sec * 12.0) * charge_factor
    r_pulsed = r * pulse

    # Cyan emission levels
    intensity = 0.6 + 0.4 * charge_factor + 0.2 * math.sin(t_sec * 20.0) * charge_factor
    glow_col = [0.0, 0.7 * intensity + 0.3 * charge_factor, 1.0 * intensity]
    
    glPushMatrix()
    glTranslatef(0.0, -0.1, 0.126) # Sits slightly forward on the palm
    
    # Main Repulsor core
    draw_sphere(r_pulsed, slices=16, stacks=16, color=glow_col, emission=glow_col)
    
    # Inner hot core
    draw_sphere(r_pulsed * 0.5, slices=12, stacks=12, color=WHITE, emission=WHITE)
    glPopMatrix()

def draw_toph_earth_core(charge_factor):
    """Renders Toph's green Earth Core on the back of the hand with expanding seismic wave rings."""
    t_sec = pygame.time.get_ticks() * 0.001
    
    # Earth pulse rate: steady earth hum, gets faster with charge
    pulse_speed = 4.0 + 6.0 * charge_factor
    pulse = 0.85 + 0.15 * math.sin(t_sec * pulse_speed)
    
    # Green core radius
    r = 0.14 + 0.06 * charge_factor
    r_pulsed = r * pulse
    
    # Earth Kingdom Emerald green glow
    glow_col = [0.0, 0.85, 0.20]
    
    glPushMatrix()
    glTranslatef(0.0, -0.1, -0.126) # Sits on the back face (negative Z)
    
    # 1. Glowing green core sphere
    draw_sphere(r_pulsed, slices=12, stacks=12, color=glow_col, emission=glow_col)
    draw_sphere(r_pulsed * 0.45, slices=10, stacks=10, color=WHITE, emission=WHITE)
    
    # 2. Seismic waves (expanding concentric rings representing seismic sense)
    glDisable(GL_LIGHTING)
    glDepthMask(GL_FALSE) # Don't write to depth buffer for transparency overlap
    
    for offset in [0.0, 0.33, 0.66]:
        progress = ((t_sec * 0.75 + offset) % 1.0)
        wave_r = 0.14 + 0.30 * progress
        alpha = 1.0 - progress
        
        # Color: Earth Green with dynamic alpha
        glColor4f(0.0, 1.0, 0.3, 0.6 * alpha)
        glLineWidth(2.0)
        
        glBegin(GL_LINE_LOOP)
        for i in range(24):
            angle = i * (2.0 * math.pi / 24.0)
            glVertex3f(math.cos(angle) * wave_r, math.sin(angle) * wave_r, -0.005)
        glEnd()
        
    glDepthMask(GL_TRUE)
    glEnable(GL_LIGHTING)
    glPopMatrix()

def draw_forearm_3d():
    """Renders the tapered cylindrical Hot-Rod Red forearm and rotating Gold wrist."""
    glPushMatrix()
    glTranslatef(0.0, -2.5, 0.0)
    glRotatef(-90.0, 1.0, 0.0, 0.0)
    
    # Forearm gauntlet cylinder
    draw_cylinder(0.52, 0.38, 1.7, slices=16, color=RED_METAL)
    glPopMatrix()

    # Golden Wrist rotation bracket
    glPushMatrix()
    glTranslatef(0.0, -0.76, 0.0)
    glRotatef(-90.0, 1.0, 0.0, 0.0)
    draw_cylinder(0.385, 0.385, 0.08, slices=24, color=GOLD_METAL)
    glPopMatrix()

def draw_finger_3d(name, anchor, base_angle, curl_val, spread_val):
    """Draws a procedural 3D articulated gauntlet finger."""
    glPushMatrix()
    
    # Move to the knuckle anchor point
    glTranslatef(anchor[0], anchor[1], anchor[2])
    
    # Apply baseline splay and lateral spread splay
    glRotatef(base_angle - 90.0, 0.0, 0.0, 1.0)
    glRotatef(spread_val, 0.0, 0.0, 1.0)
    
    # Knuckle joint weights
    JOINT_WEIGHTS = [0.50, 0.35, 0.15]
    MAX_BEND = 95.0  # Safe human bend range
    
    segments = FINGER_SEGMENTS[name]
    
    # Draw MCP joint (Golden knuckle pivot sphere)
    draw_sphere(radius=0.10, color=GOLD_METAL)
    
    for i, seg_len in enumerate(segments):
        s_len = seg_len / 65.0
        
        # Apply inward curl rotation around X-axis
        bend = curl_val * JOINT_WEIGHTS[i] * MAX_BEND
        glRotatef(-bend, 1.0, 0.0, 0.0)
        
        # Draw armored Red segment cylinder (rotated to align vertically)
        w1 = SEGMENT_WIDTHS[i][0] / 65.0
        w2 = SEGMENT_WIDTHS[i][1] / 65.0
        
        glPushMatrix()
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        draw_cylinder(w1, w2, s_len, color=RED_METAL)
        glPopMatrix()
        
        # Push coordinate frame to end of phalanx
        glTranslatef(0.0, s_len, 0.0)
        
        # Draw next joint or glowing tip
        if i < len(segments) - 1:
            draw_sphere(radius=JOINT_RADII[i+1]/65.0, color=GOLD_METAL)
        else:
            # Gold armored tip cap
            draw_sphere(radius=0.065, color=GOLD_METAL)
            # Add blue tiny repulsor emitter point at the tip
            glPushMatrix()
            glTranslatef(0.0, 0.03, 0.0)
            draw_sphere(radius=0.02, color=ICE_BLUE, emission=ICE_BLUE)
            glPopMatrix()
            
    glPopMatrix()

def draw_palm_3d(charge_factor):
    """Draws the main 3D extruded palm chassis and containment structure."""
    # Red gauntlet face
    draw_extruded_palm(PALM_VERTS, thickness=0.25, color=RED_METAL)
    
    # Gold decorative accent plates on the back
    glPushMatrix()
    glTranslatef(0.0, 0.0, -0.01)
    gold_verts = [(vx * 0.9, vy * 0.9) for vx, vy in PALM_VERTS]
    draw_extruded_palm(gold_verts, thickness=0.24, color=GOLD_METAL)
    glPopMatrix()
    
    # Gold containment ring around repulsor emitter
    glPushMatrix()
    glTranslatef(0.0, -0.1, 0.126)
    draw_ring(inner_r=0.18, outer_r=0.23, thickness=0.02, color=GOLD_METAL)
    glPopMatrix()
    
    # Repulsor light (Ice Blue, palm side of hand)
    draw_repulsor_glow(charge_factor)
    
    # Toph Earth Core copper/bronze containment ring on the back face (z = -0.126)
    glPushMatrix()
    glTranslatef(0.0, -0.1, -0.126)
    draw_ring(inner_r=0.18, outer_r=0.23, thickness=0.02, color=(0.45, 0.35, 0.25))
    glPopMatrix()
    
    # Toph Earth Core light (Green, back side of hand)
    draw_toph_earth_core(charge_factor)

# ═══════════════════════════════════════════════════════════════
#  2D HUD TEXT OVERLAYS AND BACKGROUNDS
# ═══════════════════════════════════════════════════════════════

def draw_gl_grid(tick):
    """Draws a beautiful deep cybernetic vector grid directly in OpenGL."""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WIN_W, WIN_H, 0, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Clear screen with dark carbon color
    glClearColor(0.04, 0.03, 0.025, 1.0)
    
    # Draw dark copper vector grid
    glColor3f(0.12, 0.09, 0.07)
    glLineWidth(1.0)
    glBegin(GL_LINES)
    # Vertical grid vectors
    for x in range(0, WIN_W, 40):
        glVertex2f(x, 55)
        glVertex2f(x, WIN_H - 150)
    # Horizontal grid vectors
    for y in range(55, WIN_H - 150, 40):
        glVertex2f(0, y)
        glVertex2f(WIN_W, y)
    glEnd()
    
    # Sweeping horizontal scan vector
    scan_y = 55 + (tick // 4) % (WIN_H - 150 - 55)
    
    # Soft background scan sweep area
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    glColor4f(0.0, 0.75, 1.0, 0.015)
    glVertex2f(0, scan_y - 20)
    glVertex2f(WIN_W, scan_y - 20)
    glColor4f(0.0, 0.75, 1.0, 0.04)
    glVertex2f(WIN_W, scan_y)
    glVertex2f(0, scan_y)
    glEnd()
    
    # Scanner line
    glColor3f(0.0, 0.75, 1.0)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    glVertex2f(0, scan_y)
    glVertex2f(WIN_W, scan_y)
    glEnd()
    
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

def draw_hud_overlay(hud_surf):
    """Blits the transparent Pygame telemetry/slider canvas as an OpenGL quad."""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Load Pygame HUD to temporary OpenGL texture
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    
    raw_data = pygame.image.tostring(hud_surf, "RGBA", False)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WIN_W, WIN_H, 0, GL_RGBA, GL_UNSIGNED_BYTE, raw_data)
    
    glEnable(GL_TEXTURE_2D)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WIN_W, WIN_H, 0, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glColor4f(1.0, 1.0, 1.0, 1.0)
    
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex2f(0.0, 0.0)
    glTexCoord2f(1.0, 0.0); glVertex2f(WIN_W, 0.0)
    glTexCoord2f(1.0, 1.0); glVertex2f(WIN_W, WIN_H)
    glTexCoord2f(0.0, 1.0); glVertex2f(0.0, WIN_H)
    glEnd()
    
    glDisable(GL_TEXTURE_2D)
    
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    
    glDeleteTextures(1, [tex_id])

def _draw_hud_2d_panel(surface, font_lg, font_md, font_sm, angles, mode, tick):
    """Draws the telemetry text and decorative framing on the Pygame HUD surface."""
    px, py = 14, 66
    pw, ph = 260, 280

    # 1. Semi-translucent diagnostic backplate
    pygame.draw.rect(surface, (8, 10, 15, 220), (px, py, pw, ph), border_radius=6)
    pygame.draw.rect(surface, CYAN_DIM, (px, py, pw, ph), width=1, border_radius=6)

    # Scifi corner bracket overlays
    bk = 15
    for sx, sy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        cx = px + sx * pw
        cy = py + sy * ph
        dx = 1 if sx == 0 else -1
        dy = 1 if sy == 0 else -1
        pygame.draw.line(surface, CYAN, (cx, cy), (cx + dx * bk, cy), 2)
        pygame.draw.line(surface, CYAN, (cx, cy), (cx, cy + dy * bk), 2)

    # 2. Status telemetries
    yo = py + 14
    surface.blit(font_md.render(">> CYBERNETIC DIAGNOSTIC", True, TEXT), (px + 16, yo))

    yo += 28
    surface.blit(font_sm.render("  NEURAL CORE    : ONLINE", True, GREEN), (px + 10, yo))
    yo += 17
    tc = GREEN if mode == "LIVE" else ORANGE
    tt = "LIVE" if mode == "LIVE" else "STANDBY"
    surface.blit(font_sm.render(f"  MOTION CAPTURE : {tt}", True, tc), (px + 10, yo))
    yo += 17
    surface.blit(font_sm.render("  GAUNTLET SYNC  : 99.1%", True, TEXT_DIM), (px + 10, yo))
    yo += 17
    surface.blit(font_sm.render("  GL LATENCY     : <8 ms", True, TEXT_DIM), (px + 10, yo))

    # Separation grid vector
    yo += 24
    pygame.draw.line(surface, CYAN_DIM, (px + 16, yo), (px + pw - 16, yo), 1)
    yo += 12

    # Finger splay status meters
    bar_w = 50
    for fn in FINGER_ORDER:
        ca = angles[fn]
        cfg = SERVO_CONFIG[fn]
        frac = max(0.0, min(1.0, (ca - cfg["min"]) / max(cfg["max"] - cfg["min"], 1)))

        surface.blit(font_sm.render(f"  {fn.upper():<7}: {ca:>6.1f} deg", True, CYAN), (px + 10, yo))

        bx = px + pw - bar_w - 18
        pygame.draw.rect(surface, (20, 15, 12), (bx, yo + 3, bar_w, 7), border_radius=3)
        pygame.draw.rect(surface, CYAN, (bx, yo + 3, int(frac * bar_w), 7), border_radius=3)
        yo += 19

    # Wrist angle status
    yo += 4
    wa = angles["Wrist"]
    surface.blit(font_sm.render(f"  WRIST  : {wa:>6.1f} deg", True, MAGENTA), (px + 10, yo))

def _draw_hud_header(surface, font_lg, font_md, mode):
    """Draws top system header panel."""
    pygame.draw.rect(surface, PANEL, (0, 0, WIN_W, 52))
    pygame.draw.line(surface, CYAN, (0, 52), (WIN_W, 52), 2)

    surface.blit(font_lg.render("INMOOV CYBERNETIC ARM // 3D TELEMETRY HUD", True, CYAN), (20, 14))

    mc = GREEN if mode == "LIVE" else ORANGE
    bg_col = (mc[0] // 6, mc[1] // 6, mc[2] // 6)
    pygame.draw.rect(surface, bg_col, (WIN_W - 180, 10, 160, 32), border_radius=5)
    pygame.draw.rect(surface, mc, (WIN_W - 180, 10, 160, 32), width=1, border_radius=5)
    surface.blit(font_md.render(f"SYSTEM: {mode}", True, mc), (WIN_W - 160, 17))

# ═══════════════════════════════════════════════════════════════
#  MANUAL OVERRIDE SLIDERS
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

        # Draw slider channel
        pygame.draw.rect(surface, (20, 15, 12), self.rect, border_radius=5)
        fill = pygame.Rect(self.rect.x, self.rect.y, int(frac * self.rect.w), self.rect.h)
        pygame.draw.rect(surface, CYAN, fill, border_radius=5)

        # Draw control knob
        pygame.draw.circle(surface, CYAN_MID, (knob_x, self.rect.centery), 9)
        pygame.draw.circle(surface, WHITE, (knob_x, self.rect.centery), 5)

        # Label text
        lbl = font_sm.render(f"{self.name.upper()}: {current_angle:.1f}", True, TEXT)
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
#  3D LIGHTING COMPILATION
# ═══════════════════════════════════════════════════════════════

def init_lights():
    """Initializes twin key/fill lighting with metallic specular highlights."""
    glEnable(GL_LIGHTING)
    
    # Light 0: Golden Studio Key Light (Top-Right-Front directional)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [3.0, 4.0, 5.0, 0.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.95, 0.85, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])
    
    # Light 1: Cool Cybernetic Fill Light (Bottom-Left-Back directional)
    glEnable(GL_LIGHT1)
    glLightfv(GL_LIGHT1, GL_POSITION, [-3.0, -2.0, -4.0, 0.0])
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.35, 0.45, 0.55, 1.0])
    glLightfv(GL_LIGHT1, GL_SPECULAR, [0.4, 0.5, 0.6, 1.0])
    glLightfv(GL_LIGHT1, GL_AMBIENT, [0.05, 0.05, 0.05, 1.0])

def servo_to_curl(angle, finger_name):
    """Maps absolute joint angles to normalized curl factor."""
    cfg = SERVO_CONFIG[finger_name]
    span = max(cfg["max"] - cfg["min"], 1)
    return max(0.0, min(1.0, (angle - cfg["min"]) / span))

# ═══════════════════════════════════════════════════════════════
#  MAIN WINDOW GRAPHICS LOOP
# ═══════════════════════════════════════════════════════════════

def _run_pygame():
    global _mode, _servo_angles, _flipped

    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.DOUBLEBUF | pygame.OPENGL)
    pygame.display.set_caption("InMoov Cybernetic Gauntlet // Visual 3D Simulator")
    clock = pygame.time.Clock()

    # Font resources
    font_lg = pygame.font.SysFont("consolas", 22, bold=True)
    font_md = pygame.font.SysFont("consolas", 15, bold=True)
    font_sm = pygame.font.SysFont("consolas", 12)

    # 2D drawing overlay surface
    hud_surf = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)

    # Build sliders for manual overrides
    components = (FINGER_ORDER + ["Wrist"] + [f"{f}_Spread" for f in FINGER_ORDER])
    sliders = {}
    for i, name in enumerate(components):
        row = i // 6
        col = i % 6
        gap = WIN_W // 7
        sliders[name] = Slider(gap * (col + 1) - 60, WIN_H - 108 + row * 42, 105, name)

    # 3D interactive camera coordinates
    cam_rot_x = 22.0
    cam_rot_y = -18.0
    dragging_cam = False
    tick = 0

    # Dynamic angle interpolator (lerp memory cache)
    smoothed_angles = {k: v for k, v in _servo_angles.items()}

    while True:
        clock.tick(FPS)
        tick += 1

        # ── EVENT LISTENER ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    _mode = "MANUAL" if _mode == "LIVE" else "LIVE"
                if event.key == pygame.K_f:
                    with _lock:
                        _flipped = not _flipped
                    print(f"[HUD] Render mirrored: {_flipped}")
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            # Mouse controls for rotation or sliders
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # If clicking within 3D area, trigger drag-rotation
                    if 280 <= event.pos[0] <= WIN_W and 52 <= event.pos[1] <= WIN_H - 150:
                        dragging_cam = True
                        
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging_cam = False
                    
            if event.type == pygame.MOUSEMOTION:
                if dragging_cam:
                    # Allow 3D orbital camera viewing
                    cam_rot_y += event.rel[0] * 0.4
                    cam_rot_x += event.rel[1] * 0.4
                    # Clamp vertical orbital pitch to avoid flipping upside down
                    cam_rot_x = max(-80.0, min(80.0, cam_rot_x))

            # If manual mode, let sliders intercept mouse events
            if _mode == "MANUAL":
                for name, slider in sliders.items():
                    res = slider.handle_event(event)
                    if res is not None:
                        with _lock:
                            _servo_angles[name] = res

        # Clear buffer vectors
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # ── RENDER STAGE 1: BACKDROP VECTOR GRID ──
        draw_gl_grid(tick)

        # ── RENDER STAGE 2: 3D CYBERNETIC GAUNTLET ──
        # Set Viewport bounding box to the right panel region
        glViewport(280, 150, WIN_W - 280, WIN_H - 150 - 52)
        
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)
        
        # Projection Matrix (Perspective)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (WIN_W - 280) / (WIN_H - 150 - 52), 0.1, 50.0)
        
        # Modelview Matrix
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Setup Studio Lighting
        init_lights()
        
        # Position Camera (shifted lower and further back to see finger tips fully)
        glTranslatef(0.0, -1.0, -5.5)
        glRotatef(cam_rot_x, 1.0, 0.0, 0.0)
        glRotatef(cam_rot_y, 0.0, 1.0, 0.0)
        glRotatef(180.0, 0.0, 1.0, 0.0)  # Flip hand so PALM faces viewer, not back
        
        # Dynamic splay smoothing (exponential lerp)
        with _lock:
            target_angles = dict(_servo_angles)
            
        alpha = 0.65  # Lerp weight — high = snappy real-time, low = smooth/laggy
        for k in target_angles:
            smoothed_angles[k] = smoothed_angles[k] + alpha * (target_angles[k] - smoothed_angles[k])

        wrist_rot = smoothed_angles["Wrist"] - 150.0
        
        # Determine average curl of index, middle, ring, pinky to calculate charge splay
        c_idx = servo_to_curl(smoothed_angles["Index"], "Index")
        c_mid = servo_to_curl(smoothed_angles["Middle"], "Middle")
        c_rng = servo_to_curl(smoothed_angles["Ring"], "Ring")
        c_pnk = servo_to_curl(smoothed_angles["Pinky"], "Pinky")
        avg_curl = (c_idx + c_mid + c_rng + c_pnk) / 4.0
        charge_factor = max(0.0, min(1.0, 1.0 - avg_curl)) # 1.0 = wide open (charge!), 0.0 = fist

        # Render Forearm (stationary relative to wrist rotation)
        draw_forearm_3d()

        # Render Palm and Fingers (rotates with wrist around Y-axis)
        glPushMatrix()
        glTranslatef(0.0, -0.76, 0.0)
        glRotatef(wrist_rot, 0.0, 1.0, 0.0)
        glTranslatef(0.0, 0.76, 0.0)
        
        draw_palm_3d(charge_factor)

        # Draw the 5 splayed gauntlet fingers
        for fname in FINGER_ORDER:
            curl = servo_to_curl(smoothed_angles[fname], fname)
            spread = smoothed_angles.get(f"{fname}_Spread", 0.0)

            # Re-mirror base values if HUD is flipped
            if _flipped:
                anch_off = (-FINGER_ANCHORS[fname][0], FINGER_ANCHORS[fname][1])
                base_ang = 180.0 - FINGER_BASE_ANGLES[fname]
                spr_draw = -spread
            else:
                anch_off = (FINGER_ANCHORS[fname][0], FINGER_ANCHORS[fname][1])
                base_ang = FINGER_BASE_ANGLES[fname]
                spr_draw = spread

            # Translate anchors to 3D world space bounds
            anch_3d = (anch_off[0] / 65.0, -anch_off[1] / 65.0, 0.0)
            
            draw_finger_3d(fname, anch_3d, base_ang, curl, spr_draw)

        glPopMatrix()

        # ── RENDER STAGE 3: 2D HUD OVERLAYS ──
        # Reset Viewport to cover full screen
        glViewport(0, 0, WIN_W, WIN_H)
        
        # Clear previous frame's HUD surface
        hud_surf.fill((0, 0, 0, 0))
        
        # Draw HUD headers, status logs and diagnostic panels
        _draw_hud_header(hud_surf, font_lg, font_md, _mode)
        _draw_hud_2d_panel(hud_surf, font_lg, font_md, font_sm, smoothed_angles, _mode, tick)
        
        # Draw manual override control sliders
        pygame.draw.rect(hud_surf, PANEL, (0, WIN_H - 150, WIN_W, 150))
        pygame.draw.line(hud_surf, CYAN, (0, WIN_H - 150), (WIN_W, WIN_H - 150), 2)
        hud_surf.blit(font_sm.render("MANUAL CALIBRATION OVERRIDE SLIDERS", True, TEXT_DIM), (20, WIN_H - 142))
        
        for s in sliders.values():
            s.draw(hud_surf, font_sm, smoothed_angles[s.name])
            
        # Draw drag instructions overlay
        drag_txt = "DRAG MOUSE IN VIEWPORT TO ROTATE VIEW"
        hud_surf.blit(font_sm.render(drag_txt, True, TEXT_DIM), (WIN_W - 280, 66))

        # Render composite HUD overlay quad on top
        draw_hud_overlay(hud_surf)

        pygame.display.flip()

# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    _run_pygame()
