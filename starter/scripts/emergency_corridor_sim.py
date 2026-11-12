#!/usr/bin/env python3
"""
AEGIS-EVC Emergency Green Corridor Simulation
==============================================
Simulates an ambulance traversing a 4-intersection arterial corridor
with predictive queue flushing (zero-stop green wave).

Outputs:
  1. An animated GIF  → emergency_corridor_sim.gif
  2. Frame-by-frame PNGs in ./sim_frames/
  3. A final summary PNG → emergency_corridor_summary.png
"""

import os, sys, math, itertools
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.animation import FuncAnimation, PillowWriter

# ── Configuration ─────────────────────────────────────────────────
NUM_INTERSECTIONS = 4
ROAD_Y = 5.0          # y-coordinate of the main arterial
INTERSECTION_XS = [3, 8, 13, 18]   # x positions of intersections
LANE_WIDTH = 0.6

# Ambulance
AMB_SPEED = 0.18       # units per frame (faster than normal traffic)
AMB_START_X = -2.0
AMB_Y = ROAD_Y

# Normal vehicles (queued at each intersection)
CARS_PER_INTERSECTION = 4
CAR_SPEED = 0.12       # clearing speed once light turns green

# Timing
TOTAL_FRAMES = 200
PREDICTION_HORIZON = 4.5  # units ahead to start flushing
FLUSH_TIME = 18           # frames needed to flush a queue

# Colors
COLOR_ROAD = "#2c2c2c"
COLOR_LANE_MARK = "#ffdd44"
COLOR_SIDEWALK = "#555555"
COLOR_BUILDING = "#3a3a5c"
COLOR_AMBULANCE = "#ff2222"
COLOR_AMB_STRIPE = "#ffffff"
COLOR_CAR_QUEUED = "#4488cc"
COLOR_CAR_CLEARING = "#66bb66"
COLOR_SIGNAL_RED = "#ff3333"
COLOR_SIGNAL_GREEN = "#33ff33"
COLOR_SIGNAL_YELLOW = "#ffcc00"
COLOR_BG = "#1a1a2e"
COLOR_GRASS = "#2d5a27"

# ── State objects ─────────────────────────────────────────────────
class Intersection:
    """Single intersection with traffic signal and vehicle queue."""
    def __init__(self, x, idx):
        self.x = x
        self.idx = idx
        self.state = "red"          # red | flushing | green_corridor | recovering
        self.flush_counter = 0
        self.cars = []              # list of (x, y, clearing?)
        self._init_cars()

    def _init_cars(self):
        """Place queued cars behind the intersection stop line."""
        for i in range(CARS_PER_INTERSECTION):
            cx = self.x - 1.0 - i * 0.9
            cy = ROAD_Y + LANE_WIDTH * 0.5  # upper lane (same direction as ambulance approach)
            self.cars.append({"x": cx, "y": cy, "clearing": False, "gone": False})

    @property
    def signal_color(self):
        if self.state == "red":
            return COLOR_SIGNAL_RED
        if self.state == "flushing":
            return COLOR_SIGNAL_YELLOW  # transitional flush phase
        if self.state == "green_corridor":
            return COLOR_SIGNAL_GREEN
        return COLOR_SIGNAL_RED  # recovering

class Ambulance:
    def __init__(self):
        self.x = AMB_START_X
        self.y = AMB_Y - LANE_WIDTH * 0.5  # lower lane (eastbound priority)
        self.active = True
        self.passed_intersections = set()

# ── Build scene ───────────────────────────────────────────────────
intersections = [Intersection(x, i) for i, x in enumerate(INTERSECTION_XS)]
ambulance = Ambulance()

# ── Drawing helpers ───────────────────────────────────────────────
def draw_road(ax):
    """Draw the arterial road, lane markings, sidewalks, grass."""
    # grass background
    ax.set_facecolor(COLOR_BG)
    ax.fill_between([-3, 22], 0, 10, color=COLOR_GRASS, alpha=0.25)

    # road surface
    road_bottom = ROAD_Y - 1.2
    road_top = ROAD_Y + 1.2
    ax.fill_between([-3, 22], road_bottom, road_top, color=COLOR_ROAD)

    # lane markings (dashed center line)
    for xm in np.arange(-3, 22, 0.8):
        ax.plot([xm, xm + 0.4], [ROAD_Y, ROAD_Y], color=COLOR_LANE_MARK,
                linewidth=1, alpha=0.6)

    # sidewalks
    ax.fill_between([-3, 22], road_top, road_top + 0.3, color=COLOR_SIDEWALK, alpha=0.5)
    ax.fill_between([-3, 22], road_bottom - 0.3, road_bottom, color=COLOR_SIDEWALK, alpha=0.5)

    # cross streets at each intersection
    for ix in INTERSECTION_XS:
        ax.fill_between([ix - 0.4, ix + 0.4], 0, road_bottom, color=COLOR_ROAD, alpha=0.6)
        ax.fill_between([ix - 0.4, ix + 0.4], road_top, 10, color=COLOR_ROAD, alpha=0.6)

    # decorative buildings
    for bx in [0, 5.5, 10.5, 15.5, 20]:
        ax.add_patch(FancyBboxPatch((bx, road_top + 0.5), 1.5, 1.2,
                                     boxstyle="round,pad=0.1",
                                     facecolor=COLOR_BUILDING, edgecolor="#555", linewidth=0.5, alpha=0.7))
        ax.add_patch(FancyBboxPatch((bx, road_bottom - 1.7), 1.5, 1.2,
                                     boxstyle="round,pad=0.1",
                                     facecolor=COLOR_BUILDING, edgecolor="#555", linewidth=0.5, alpha=0.7))


def draw_signal(ax, inter):
    """Draw traffic signal head above the intersection."""
    sx, sy = inter.x, ROAD_Y + 1.8
    # signal pole
    ax.plot([inter.x, inter.x], [ROAD_Y + 1.2, sy], color="#888", linewidth=2)
    # signal head
    ax.add_patch(Circle((sx, sy), 0.25, facecolor=inter.signal_color,
                          edgecolor="#222", linewidth=1.5, zorder=5))
    # label
    ax.text(sx, sy + 0.55, f"J{inter.idx+1}", ha="center", va="bottom",
            fontsize=7, color="white", fontweight="bold")


def draw_car(ax, car):
    """Draw a single passenger vehicle."""
    if car["gone"]:
        return
    c = COLOR_CAR_CLEARING if car["clearing"] else COLOR_CAR_QUEUED
    ax.add_patch(FancyBboxPatch((car["x"] - 0.35, car["y"] - 0.18), 0.7, 0.36,
                                 boxstyle="round,pad=0.05",
                                 facecolor=c, edgecolor="#222", linewidth=0.7, zorder=4))


def draw_ambulance(ax, amb):
    """Draw the ambulance with a flashing light effect."""
    if not amb.active:
        return
    # body
    ax.add_patch(FancyBboxPatch((amb.x - 0.5, amb.y - 0.22), 1.0, 0.44,
                                 boxstyle="round,pad=0.06",
                                 facecolor=COLOR_AMBULANCE, edgecolor="#fff",
                                 linewidth=1.5, zorder=6))
    # white cross
    ax.plot([amb.x - 0.15, amb.x + 0.15], [amb.y, amb.y], color=COLOR_AMB_STRIPE,
            linewidth=2.5, zorder=7)
    ax.plot([amb.x, amb.x], [amb.y - 0.12, amb.y + 0.12], color=COLOR_AMB_STRIPE,
            linewidth=2.5, zorder=7)
    # siren flash (alternating blue/red glow)
    flash_color = "#3399ff" if (int(amb.x * 10) % 2 == 0) else "#ff3333"
    ax.add_patch(Circle((amb.x + 0.35, amb.y + 0.22), 0.1,
                          facecolor=flash_color, edgecolor="none", alpha=0.9, zorder=7))


def draw_prediction_zone(ax, amb):
    """Draw the look-ahead prediction zone."""
    if not amb.active or amb.x > INTERSECTION_XS[-1] + 2:
        return
    zone_left = amb.x + 0.5
    zone_right = amb.x + PREDICTION_HORIZON + 0.5
    ax.fill_between([zone_left, zone_right],
                     ROAD_Y - 1.0, ROAD_Y + 1.0,
                     color="#ffaa00", alpha=0.08, zorder=2)
    ax.plot([zone_right, zone_right], [ROAD_Y - 1.0, ROAD_Y + 1.0],
            color="#ffaa00", linewidth=1, linestyle="--", alpha=0.5, zorder=2)
    ax.text(zone_right, ROAD_Y + 1.1, "Prediction\nHorizon", ha="center",
            fontsize=5, color="#ffaa00", alpha=0.7)


def draw_hud(ax, frame, amb):
    """Draw heads-up display with timing info."""
    # Title
    ax.text(10, 9.3, "AEGIS-EVC  Emergency Green Corridor Simulation",
            ha="center", va="top", fontsize=11, color="white", fontweight="bold",
            fontfamily="monospace")

    # Status bar
    if amb.active and amb.x <= INTERSECTION_XS[-1] + 2:
        eta_to_next = None
        for ix in INTERSECTION_XS:
            if ix > amb.x + 0.5:
                eta_to_next = (ix - amb.x) / AMB_SPEED
                break
        eta_str = f"ETA next: {eta_to_next:.0f}f" if eta_to_next else "PASSED ALL"
        status = f"Frame {frame:03d}  |  Ambulance X={amb.x:.1f}  |  Speed={AMB_SPEED:.2f}u/f  |  {eta_str}"
    elif amb.x > INTERSECTION_XS[-1] + 2:
        status = f"Frame {frame:03d}  |  ✅ CORRIDOR CLEARED — Zero-stop passage achieved!"
    else:
        status = f"Frame {frame:03d}"

    ax.text(10, 0.5, status, ha="center", va="bottom", fontsize=7,
            color="#aaddff", fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#000000", alpha=0.6, edgecolor="#444"))

    # Legend
    legend_y = 8.6
    legend_items = [
        (COLOR_AMBULANCE, "Ambulance (V2X)"),
        (COLOR_CAR_QUEUED, "Queued Vehicle"),
        (COLOR_CAR_CLEARING, "Clearing Vehicle"),
        (COLOR_SIGNAL_GREEN, "Green (Corridor)"),
        (COLOR_SIGNAL_YELLOW, "Flushing Phase"),
        (COLOR_SIGNAL_RED, "Red / Normal"),
    ]
    for i, (color, label) in enumerate(legend_items):
        lx = 0.3 + (i % 3) * 6.8
        ly = legend_y - (i // 3) * 0.45
        ax.add_patch(FancyBboxPatch((lx, ly - 0.1), 0.3, 0.2,
                                     boxstyle="round,pad=0.02",
                                     facecolor=color, edgecolor="#555", linewidth=0.5))
        ax.text(lx + 0.45, ly, label, fontsize=6, color="#cccccc", va="center")


# ── Simulation logic ──────────────────────────────────────────────
def update_state(frame):
    """Advance simulation by one frame."""
    # Move ambulance
    if ambulance.active:
        ambulance.x += AMB_SPEED
        if ambulance.x > 22:
            ambulance.active = False

    # For each intersection: check if ambulance is within prediction horizon
    for inter in intersections:
        dist = inter.x - ambulance.x
        if inter.state == "red" and 0 < dist < PREDICTION_HORIZON + 1.5:
            # Start flushing
            inter.state = "flushing"
            inter.flush_counter = 0
            for car in inter.cars:
                car["clearing"] = True

        if inter.state == "flushing":
            inter.flush_counter += 1
            # Move cars out of the way (turn right / accelerate forward)
            for car in inter.cars:
                if not car["gone"]:
                    car["y"] += 0.12  # move to cross-street (upward)
                    car["x"] += 0.04
                    if car["y"] > ROAD_Y + 2.0:
                        car["gone"] = True
            # After enough time, switch to full green corridor
            if inter.flush_counter >= FLUSH_TIME:
                inter.state = "green_corridor"

        if inter.state == "green_corridor":
            # Check if ambulance has passed
            if ambulance.x > inter.x + 1.5:
                inter.state = "recovering"
                inter.flush_counter = 0
                ambulance.passed_intersections.add(inter.idx)

        if inter.state == "recovering":
            inter.flush_counter += 1
            if inter.flush_counter > 20:
                inter.state = "red"  # back to normal


# ── Animation ─────────────────────────────────────────────────────
print("🚑 AEGIS-EVC Emergency Green Corridor Simulation")
print("=" * 55)
print(f"  Intersections : {NUM_INTERSECTIONS} (J1–J4)")
print(f"  Cars/junction : {CARS_PER_INTERSECTION}")
print(f"  Total frames  : {TOTAL_FRAMES}")
print(f"  Ambulance speed: {AMB_SPEED} units/frame")
print(f"  Prediction horizon: {PREDICTION_HORIZON} units ahead")
print()

fig, ax = plt.subplots(1, 1, figsize=(16, 6), dpi=100)
fig.patch.set_facecolor(COLOR_BG)

# Output directory
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim_output")
os.makedirs(out_dir, exist_ok=True)
frames_dir = os.path.join(out_dir, "frames")
os.makedirs(frames_dir, exist_ok=True)

key_frames = []

def render_frame(frame):
    ax.clear()
    ax.set_xlim(-3, 22)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")

    update_state(frame)

    draw_road(ax)
    draw_prediction_zone(ax, ambulance)
    for inter in intersections:
        draw_signal(ax, inter)
        for car in inter.cars:
            draw_car(ax, car)
    draw_ambulance(ax, ambulance)
    draw_hud(ax, frame, ambulance)

    return []


def save_key_frames():
    """Save snapshots at important moments."""
    # Reset state for key-frame capture
    global intersections, ambulance
    scenarios = [
        (0,   "01_initial_state"),
        (15,  "02_prediction_detected"),
        (35,  "03_j1_flushing"),
        (55,  "04_j1_green_corridor"),
        (80,  "05_j2_flushing"),
        (110, "06_mid_corridor"),
        (150, "07_j3_j4_clearing"),
        (190, "08_corridor_complete"),
    ]

    for target_frame, label in scenarios:
        # Reset
        intersections = [Intersection(x, i) for i, x in enumerate(INTERSECTION_XS)]
        ambulance = Ambulance()

        for f in range(target_frame + 1):
            ax.clear()
            ax.set_xlim(-3, 22)
            ax.set_ylim(0, 10)
            ax.set_aspect("equal")
            ax.axis("off")
            update_state(f)

        # Draw final state
        draw_road(ax)
        draw_prediction_zone(ax, ambulance)
        for inter in intersections:
            draw_signal(ax, inter)
            for car in inter.cars:
                draw_car(ax, car)
        draw_ambulance(ax, ambulance)
        draw_hud(ax, target_frame, ambulance)

        fpath = os.path.join(frames_dir, f"{label}.png")
        fig.savefig(fpath, bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=120)
        print(f"  ✅ Saved key frame: {label}.png")
        key_frames.append(fpath)


# Save key frames first
print("📸 Saving key frames...")
save_key_frames()

# Now build animated GIF
print("\n🎬 Building animated GIF (this may take a minute)...")
intersections = [Intersection(x, i) for i, x in enumerate(INTERSECTION_XS)]
ambulance = Ambulance()

anim = FuncAnimation(fig, render_frame, frames=TOTAL_FRAMES, interval=50, blit=False)
gif_path = os.path.join(out_dir, "emergency_corridor_sim.gif")
anim.save(gif_path, writer=PillowWriter(fps=20))
print(f"  ✅ Animated GIF saved: {gif_path}")

# Build summary panel (2x4 grid of key frames)
print("\n📊 Building summary panel...")
fig2, axes = plt.subplots(2, 4, figsize=(20, 7), dpi=120)
fig2.patch.set_facecolor(COLOR_BG)
fig2.suptitle("AEGIS-EVC Emergency Green Corridor — Simulation Timeline",
              fontsize=14, color="white", fontweight="bold", y=0.98)

for idx, (fpath, axs) in enumerate(zip(key_frames, axes.flat)):
    img = plt.imread(fpath)
    axs.imshow(img)
    axs.axis("off")
    axs.set_title(os.path.basename(fpath).replace(".png", "").replace("_", " "),
                  fontsize=7, color="#aaddff", pad=3)

plt.tight_layout(rect=[0, 0, 1, 0.95])
summary_path = os.path.join(out_dir, "emergency_corridor_summary.png")
fig2.savefig(summary_path, bbox_inches="tight", facecolor=fig2.get_facecolor(), dpi=120)
print(f"  ✅ Summary panel saved: {summary_path}")

print("\n" + "=" * 55)
print("🏁 Simulation complete!")
print(f"   Output directory: {out_dir}")
print(f"   Key frames: {len(key_frames)} snapshots")
print(f"   Animation: {gif_path}")
print(f"   Summary: {summary_path}")
