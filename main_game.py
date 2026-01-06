import pygame
import threading
import sys
import os

# --- IMPORT TRACKING SCRIPT ---
import motion_tracking as mt

# --- CONFIGURATION ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
TARGET_REPS = 12
# Animation Speed: 0.15 is good for 3 frames (cycles cleanly)
ANIMATION_SPEED = 0.15

# Colors
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
RED = (220, 20, 60)
GREEN = (34, 139, 34)
BLACK = (0, 0, 0)

# --- INITIALIZATION ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Group 6: Gamified Strength Trainer")

# Fonts
font_ui = pygame.font.SysFont("Arial", 28, bold=True)
font_big = pygame.font.SysFont("Arial", 60, bold=True)
font_msg = pygame.font.SysFont("Arial", 40, bold=True)

# --- ASSET LOADING ---

# 1. Load Bird Images
bird_up_img = None
bird_down_img = None
try:
    bird_up_img = pygame.image.load("bird_up.png")
    bird_up_img = pygame.transform.scale(bird_up_img, (80, 60))

    bird_down_img = pygame.image.load("bird_down.png")
    bird_down_img = pygame.transform.scale(bird_down_img, (80, 60))
except FileNotFoundError:
    print("Warning: bird images not found. Using shapes.")

# 2. Load Feedback Animation (3 Frames)
# Looks for: guide_0.png (Down), guide_1.png (Halfway), guide_2.png (Up)
feedback_frames = []
frame_index = 0
try:
    # UPDATED: Loop for 10 frames only
    for i in range(10):
        filename = f"frame_0{i}_delay-0.2s.png"
        if os.path.exists(filename):
            img = pygame.image.load(filename)
            img = pygame.transform.scale(img, (300, 200))  # Size of the popup
            feedback_frames.append(img)
            print(f"Loaded {filename}")
        else:
            print(f"Warning: Could not find {filename}")
except Exception as e:
    print(f"Animation Load Error: {e}")

# Fallback if no frames found
if not feedback_frames:
    try:
        static_img = pygame.image.load("frame_04_delay-0.2s.png")
        static_img = pygame.transform.scale(static_img, (300, 200))
        feedback_frames.append(static_img)
    except:
        pass

    # --- TRACKING THREAD ---


def start_tracking_thread():
    try:
        mt.main()
    except Exception as e:
        print(f"Tracking Error: {e}")


t = threading.Thread(target=start_tracking_thread, daemon=True)
t.start()


# --- HELPER FUNCTIONS ---
def get_normalized_wrist_height():
    if mt.latest_result and mt.latest_result.pose_landmarks:
        try:
            landmarks = mt.latest_result.pose_landmarks[0]
            left_y = landmarks[15].y
            right_y = landmarks[16].y
            avg_y = (left_y + right_y) / 2
            # Map Physical Y (0.8=down, 0.2=up) to Game Logic (0.0 - 1.0)
            mapped_y = (avg_y - 0.2) / (0.8 - 0.2)
            return max(0.0, min(1.0, mapped_y))
        except:
            return 0.5
    return 0.5


# --- MAIN LOOP ---
clock = pygame.time.Clock()
running = True
previous_bird_y = SCREEN_HEIGHT // 2

while running:
    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 2. Logic Update
    wrist_height = get_normalized_wrist_height()

    # Calculate Target Y
    target_bird_y = int(wrist_height * (SCREEN_HEIGHT - 100)) + 50

    # Smooth Movement (Lerp)
    current_bird_y = previous_bird_y + (target_bird_y - previous_bird_y) * 0.2

    # Determine Bird State
    if current_bird_y < previous_bird_y - 1:  # Moving UP
        is_flying_up = True
    else:
        is_flying_up = False

    previous_bird_y = current_bird_y

    # 3. Drawing
    screen.fill(SKY_BLUE)

    # Draw Goal Line
    pygame.draw.line(screen, GREEN, (0, 100), (SCREEN_WIDTH, 100), 5)
    goal_label = font_ui.render("GOAL HEIGHT", True, GREEN)
    screen.blit(goal_label, (10, 70))

    # --- DRAW BIRD ---
    if bird_up_img and bird_down_img:
        if is_flying_up:
            screen.blit(bird_up_img, (SCREEN_WIDTH // 2 - 40, int(current_bird_y) - 30))
        else:
            screen.blit(bird_down_img, (SCREEN_WIDTH // 2 - 40, int(current_bird_y) - 30))
    else:
        # Fallback Shape
        color = (255, 215, 0)
        if is_flying_up: color = (255, 100, 0)
        pygame.draw.circle(screen, color, (SCREEN_WIDTH // 2, int(current_bird_y)), 30)
        pygame.draw.circle(screen, BLACK, (SCREEN_WIDTH // 2 + 10, int(current_bird_y) - 10), 5)

    # --- DRAW UI ---
    score_box_w, score_box_h = 250, 100
    pygame.draw.rect(screen, WHITE, (20, 20, score_box_w, score_box_h), border_radius=10)
    pygame.draw.rect(screen, BLACK, (20, 20, score_box_w, score_box_h), 2, border_radius=10)

    reps_text = font_ui.render(f"Reps: {mt.lateral_raise_count} / {TARGET_REPS}", True, BLACK)
    points_text = font_ui.render(f"Score: {mt.lateral_raise_count * 100}", True, BLACK)

    screen.blit(reps_text, (40, 40))
    screen.blit(points_text, (40, 80))

    # --- DRAW FEEDBACK (3-FRAME ANIMATION) ---
    if mt.incorrect_form_detected:
        # Red Border Overlay
        pygame.draw.rect(screen, RED, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 10)

        # Text Warning
        warn_surf = font_msg.render("WRONG FORM!", True, RED)
        screen.blit(warn_surf, (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2))

        # Show Animated Frames
        if len(feedback_frames) > 0:
            # Draw Background box for the image
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 320, SCREEN_HEIGHT - 220, 310, 210))

            # Update Frame Index
            frame_index += ANIMATION_SPEED

            # Loop back to 0 if we pass the last frame
            if frame_index >= len(feedback_frames):
                frame_index = 0

            # Draw the current frame
            current_img = feedback_frames[int(frame_index)]
            screen.blit(current_img, (SCREEN_WIDTH - 315, SCREEN_HEIGHT - 215))
        else:
            # Fallback red box
            pygame.draw.rect(screen, RED, (SCREEN_WIDTH - 220, SCREEN_HEIGHT - 220, 200, 200), 2)

    # Victory Screen
    if mt.lateral_raise_count >= TARGET_REPS:
        win_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        win_overlay.set_alpha(200)
        win_overlay.fill(GREEN)
        screen.blit(win_overlay, (0, 0))
        win_text = font_big.render("WORKOUT COMPLETE!", True, WHITE)
        screen.blit(win_text, (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 50))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()