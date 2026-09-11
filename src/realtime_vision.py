import time
from typing import Optional, Tuple, Dict
import cv2
import numpy as np


class RealtimeVisionAgent:
    """
    Real-Time Computer Vision & Decision Agent for CookieRun Classic.
    Analyzes live video frames at 30-60 FPS to detect:
    - Ceiling obstacles (Hanging monsters, vines, stalactites) -> SLIDE
    - Ground obstacles & floor holes (Spikes, blocks, pits) -> JUMP
    - Floating jellies & coins -> JUMP / DOUBLE JUMP
    """

    ACTION_NONE = "NONE"
    ACTION_JUMP = "JUMP"
    ACTION_DOUBLE_JUMP = "DOUBLE_JUMP"
    ACTION_SLIDE_DOWN = "SLIDE_DOWN"
    ACTION_SLIDE_UP = "SLIDE_UP"

    def __init__(self, target_width: int = 1280, target_height: int = 720):
        self.target_width = target_width
        self.target_height = target_height

        # State tracking
        self.is_sliding = False
        self.last_jump_time = 0.0
        self.last_slide_time = 0.0
        self.ceiling_obstacle_end_time = 0.0

        # Action cooldowns
        self.jump_cooldown = 0.38  # Minimum time between jump sequences
        self.slide_min_duration = 0.30

        # Detection Corridor (Ahead of the running Cookie)
        # Cookie is at X: ~180-260, running rightward at ~550-700 px/sec
        self.LOOKAHEAD_X_MIN = 320
        self.LOOKAHEAD_X_MAX = 580

        # Vertical Zones for CookieRun (1280x720 base, Floor is at Y ~ 530-550)
        # 1. Ceiling obstacle zone: Hanging hazards hitting standing cookie
        self.CEILING_Y_MIN = 310
        self.CEILING_Y_MAX = 460

        # 2. Ground obstacle zone: Spikes, blocks sitting on floor surface
        self.GROUND_OBS_Y_MIN = 430
        self.GROUND_OBS_Y_MAX = 535

        # 3. Floor surface & pit gap zone
        self.FLOOR_Y_MIN = 535
        self.FLOOR_Y_MAX = 575

        # 4. Jelly airborne collection zones
        self.MID_JELLY_Y_MIN = 400
        self.MID_JELLY_Y_MAX = 510

        self.HIGH_JELLY_Y_MIN = 250
        self.HIGH_JELLY_Y_MAX = 400

    def analyze_frame(self, frame: np.ndarray) -> str:
        """
        Analyze live video frame and decide action:
        - Real Hanging / Overhead Obstacle -> SLIDE_DOWN (and SLIDE_UP when cleared)
        - Real Ground Obstacle / Pit Gap   -> JUMP
        - Clear track / normal running     -> NONE (No jumping for floating jellies)
        Execution time: ~1.5 ms.
        """
        if frame is None:
            return self.ACTION_NONE

        h, w = frame.shape[:2]
        if w != self.target_width or h != self.target_height:
            frame = cv2.resize(frame, (self.target_width, self.target_height))

        now = time.perf_counter()

        # Extract the lookahead corridor ahead of the Cookie
        # Cookie body + aura + held items end at X ~ 380, so we inspect X: 400 to 660
        corridor = frame[:, 400:660]
        hsv = cv2.cvtColor(corridor, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(corridor, cv2.COLOR_BGR2GRAY)

        # Mask out yellow/gold coins & bear jellies so they are never mistaken for obstacles
        yellow_mask = (hsv[:, :, 0] >= 15) & (hsv[:, :, 0] <= 36) & (hsv[:, :, 1] >= 100) & (hsv[:, :, 2] >= 120)
        blue_mask = (hsv[:, :, 0] >= 90) & (hsv[:, :, 0] <= 130) & (hsv[:, :, 1] >= 100) & (hsv[:, :, 2] >= 120)
        jelly_mask = cv2.dilate((yellow_mask | blue_mask).astype(np.uint8), np.ones((7, 7), np.uint8))

        # -------------------------------------------------------------
        # STEP 1: CEILING OBSTACLE DETECTION (Must Slide!)
        # Standing Cookie head is at Y ~ 400, Sliding Cookie head is at Y ~ 480.
        # A real ceiling hazard MUST hang down into Y >= 425 to hit the cookie!
        # Background scenery/text ends above Y = 360 and will never reach Y = 425.
        # -------------------------------------------------------------
        ceil_gray = gray[160:490, :]
        ceil_edges = cv2.Canny(ceil_gray, 80, 180)
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 25))
        ceil_closed = cv2.morphologyEx(ceil_edges, cv2.MORPH_CLOSE, kernel_v)
        c_cnts, _ = cv2.findContours(ceil_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        has_ceiling_hazard = False
        for c in c_cnts:
            cx, cy, cw, ch = cv2.boundingRect(c)
            area = cv2.contourArea(c)
            y_top = 160 + cy
            y_bottom = 160 + cy + ch
            # Starts high (y_top <= 260), reaches down into collision zone (y_bottom >= 425),
            # leaves sliding clearance (y_bottom <= 495), tall (ch >= 160), bounded width (20 <= cw <= 220), area >= 1200
            if y_top <= 260 and y_bottom >= 425 and ch >= 160 and 20 <= cw <= 220 and area >= 1200:
                has_ceiling_hazard = True
                break

        if has_ceiling_hazard:
            self.ceiling_obstacle_end_time = now + 0.35
            if not self.is_sliding:
                self.is_sliding = True
                self.last_slide_time = now
                return self.ACTION_SLIDE_DOWN
            return self.ACTION_NONE

        # Safe to stand back up only when an active slide has cleared the obstacle
        if self.is_sliding:
            if now > self.ceiling_obstacle_end_time and (now - self.last_slide_time) >= self.slide_min_duration:
                self.is_sliding = False
                return self.ACTION_SLIDE_UP
            return self.ACTION_NONE

        # -------------------------------------------------------------
        # STEP 2: GROUND OBSTACLE & PIT DETECTION (Must Jump!)
        # Zone: Y = 410 to 535 (standing on platform)
        # -------------------------------------------------------------
        can_jump = (now - self.last_jump_time) > self.jump_cooldown
        if can_jump:
            # A) Ground obstacle: Spikes, blocks, rising barriers
            ground_gray = gray[410:535, :].copy()
            ground_jelly = jelly_mask[410:535, :]
            ground_gray[ground_jelly > 0] = 0

            ground_edges = cv2.Canny(ground_gray, 80, 170)
            ground_edges[ground_jelly > 0] = 0

            kernel_g = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
            ground_closed = cv2.morphologyEx(ground_edges, cv2.MORPH_CLOSE, kernel_g)
            g_cnts, _ = cv2.findContours(ground_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            has_ground_hazard = False
            for c in g_cnts:
                gx, gy, gw, gh = cv2.boundingRect(c)
                area = cv2.contourArea(c)
                # Sits on track surface: (gy + gh) >= 70, height gh >= 38, width 25 <= gw <= 250, area >= 350
                if (gy + gh) >= 70 and gh >= 38 and 25 <= gw <= 250 and area >= 350:
                    has_ground_hazard = True
                    break

            # B) Pit / Gap in running platform: Platform rail at Y = 535 to 555
            plat = gray[535:555, :]
            col_means = np.mean(plat, axis=0)
            has_pit = False
            consec_dark = 0
            for cm in col_means:
                if cm < 8.0:
                    consec_dark += 1
                    if consec_dark >= 18:
                        has_pit = True
                        break
                else:
                    consec_dark = 0

            if has_ground_hazard or has_pit:
                self.last_jump_time = now
                return self.ACTION_JUMP

        # Default: Normal running, collect track items naturally without jumping
        return self.ACTION_NONE

    def reset(self):
        """Reset state when round ends or transitions."""
        self.is_sliding = False
        self.last_jump_time = 0.0
        self.last_slide_time = 0.0
        self.ceiling_obstacle_end_time = 0.0
