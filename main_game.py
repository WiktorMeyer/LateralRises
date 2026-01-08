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
ANIMATION_SPEED = 0.25
FEEDBACK_DURATION = 2000  # GIF lingers for 3 seconds

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
print("--- LOADING ASSETS ---")

# 1. Load Bird Images
bird_up_img = None
bird_down_img = None
try:
    if os.path.exists("bird_up.png"):
        bird_up_img = pygame.image.load("bird_up.png")
        bird_up_img = pygame.transform.scale(bird_up_img, (80, 60))

    if os.path.exists("bird_down.png"):
        bird_down_img = pygame.image.load("bird_down.png")
        bird_down_img = pygame.transform.scale(bird_down_img, (80, 60))
except FileNotFoundError:
    print("Warning: bird images not found.")

# 2. Load Feedback Animation (10 Frames)
feedback_frames = []
frame_index = 0

# Check for frame_00... to frame_09...
# Tries to load from root folder first
for i in range(10):
    # Adjust this filename pattern if yours is different!
    filename = f"frame_{str(i).zfill(2)}_delay-0.2s.png"

    if os.path.exists(filename):
        try:
            img = pygame.image.load(filename)
            img = pygame.transform.scale(img, (300, 200))
            feedback_frames.append(img)
            print(f"Loaded: {filename}")
        except Exception as e:
            print(f"Error loading {filename}: {e}")

if len(feedback_frames) == 0:
    print("WARNING: No animation frames found! Feedback will be a red box.")


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
            mapped_y = (avg_y - 0.2) / (0.8 - 0.2)
            return max(0.0, min(1.0, mapped_y))
        except:
            return 0.5
    return 0.5


# --- MAIN LOOP ---
clock = pygame.time.Clock()
running = True
previous_bird_y = SCREEN_HEIGHT // 2
debug_trigger = False

# TIMER VARIABLE
feedback_end_time = 0

print("--- GAME STARTED ---")

while running:
    current_time = pygame.time.get_ticks()

    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Spacebar simulates incorrect form for testing
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Set timer for 3 seconds in future
                feedback_end_time = current_time + FEEDBACK_DURATION
                debug_trigger = True  # Trigger the red text momentarily

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                debug_trigger = False  # Stop red text when key released

    # 2. Logic Update
    wrist_height = get_normalized_wrist_height()
    target_bird_y = int(wrist_height * (SCREEN_HEIGHT - 100)) + 50
    current_bird_y = previous_bird_y + (target_bird_y - previous_bird_y) * 0.2

    if current_bird_y < previous_bird_y - 1:
        is_flying_up = True
    else:
        is_flying_up = False

    previous_bird_y = current_bird_y

    # --- TIMER LOGIC ---
    # If form is wrong NOW, update the "end time" so the GIF stays alive.
    if mt.incorrect_form_detected:
        feedback_end_time = current_time + FEEDBACK_DURATION

    # Check if we should show the GIF (lingering)
    show_gif = current_time < feedback_end_time

    # Check if we should show the Red Text (immediate only)
    show_red_alert = mt.incorrect_form_detected or debug_trigger

    # 3. Drawing
    screen.fill(SKY_BLUE)

    # Goal Line
    pygame.draw.line(screen, GREEN, (0, 100), (SCREEN_WIDTH, 100), 5)
    goal_label = font_ui.render("GOAL HEIGHT", True, GREEN)
    screen.blit(goal_label, (10, 70))

    # Draw Bird
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

    # UI Box
    score_box_w, score_box_h = 250, 100
    pygame.draw.rect(screen, WHITE, (20, 20, score_box_w, score_box_h), border_radius=10)
    pygame.draw.rect(screen, BLACK, (20, 20, score_box_w, score_box_h), 2, border_radius=10)

    reps_text = font_ui.render(f"Reps: {mt.lateral_raise_count} / {TARGET_REPS}", True, BLACK)
    points_text = font_ui.render(f"Score: {mt.lateral_raise_count * 100}", True, BLACK)

    screen.blit(reps_text, (40, 40))
    screen.blit(points_text, (40, 80))

    # --- PART 1: IMMEDIATE FEEDBACK (Red Text & Border) ---
    # Only shows while form is ACTUALLY wrong
    if show_red_alert:
        # Red Border
        pygame.draw.rect(screen, RED, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 10)

        # Warning Text (Center)
        warn_surf = font_msg.render("WRONG FORM!", True, RED)
        screen.blit(warn_surf, (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2))

    # --- PART 2: LINGERING FEEDBACK (Animation) ---
    # Shows for 3 seconds even after form is fixed
    if show_gif:
        # Animation Box Position (BOTTOM LEFT)
        anim_x = 20
        anim_y = SCREEN_HEIGHT - 220

        if len(feedback_frames) > 0:
            # White background
            pygame.draw.rect(screen, WHITE, (anim_x - 5, anim_y - 5, 310, 210))

            # Animation Logic
            frame_index += ANIMATION_SPEED
            if frame_index >= len(feedback_frames):
                frame_index = 0

            # Draw current frame
            current_img = feedback_frames[int(frame_index)]
            screen.blit(current_img, (anim_x, anim_y))
        else:
            # Fallback Red Box
            pygame.draw.rect(screen, RED, (anim_x, anim_y, 300, 200), 2)
            err_text = font_ui.render("Images Missing", True, RED)
            screen.blit(err_text, (anim_x + 50, anim_y + 90))

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
#quit game
pygame.quit()
sys.exit()