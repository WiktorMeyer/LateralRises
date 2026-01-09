import pygame
import threading
import sys
import os
import cv2
import numpy as np

# --- IMPORT TRACKING SCRIPT ---
import motion_tracking as mt

# --- CONFIGURATION ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FEEDBACK_DURATION = 3000
REST_DURATION = 5000

BIRD_Y = SCREEN_HEIGHT // 2

# Colors
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
RED = (220, 20, 60)
GREEN = (34, 139, 34)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
YELLOW = (255, 215, 0)
ORANGE = (255, 140, 0)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)

# --- INITIALIZATION ---
pygame.init()
pygame.mixer.init()  # Initialize the mixer for audio
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Group 6: Bird Game V2 (Video Guide)")

# Fonts
font_ui = pygame.font.SysFont("Arial", 28, bold=True)
font_big = pygame.font.SysFont("Arial", 60, bold=True)
font_msg = pygame.font.SysFont("Arial", 40, bold=True)
font_small = pygame.font.SysFont("Arial", 22)

# Game States
game_state = 'MENU'
target_reps = 10
target_sets = 3
current_set = 1
reps_at_start_of_set = 0
rest_end_time = 0

# --- VIDEO GUIDE SETUP ---
video_path = "video tutorial.mp4"  # Ensure this file exists!
audio_path = "tutorial_audio.wav"  # Audio file for the tutorial
cap_guide = None
tutorial_audio = None


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
            # Average height for body position
            avg_y = (landmarks[15].y + landmarks[16].y) / 2
            mapped_y = (avg_y - 0.2) / (0.8 - 0.2)
            return max(0.0, min(1.0, mapped_y))
        except:
            return 0.5
    return 0.5


def draw_button(rect, text, hover=False, color=BUTTON_COLOR):
    draw_col = BUTTON_HOVER if hover else color
    pygame.draw.rect(screen, draw_col, rect, border_radius=10)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=10)
    text_surf = font_ui.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)


def draw_text_centered(text, font, color, y_offset):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
    screen.blit(surf, rect)


# --- NEW: DYNAMIC BIRD DRAWING ---
def draw_dynamic_bird(surface, x, y, left_up, right_up, left_wrist_height, right_wrist_height):
    """
    Draws a bird where wings respond individually to arm states.
    x, y: Center position of the bird body.
    left_up: Boolean (True if user's left arm is raised)
    right_up: Boolean (True if user's right arm is raised)
    """
    # 1. Body
    pygame.draw.circle(surface, YELLOW, (x, y), 40)  # Body
    pygame.draw.circle(surface, BLACK, (x, y), 40, 3)  # Outline

    # 2. Eyes
    pygame.draw.circle(surface, WHITE, (x - 15, y - 10), 10)
    pygame.draw.circle(surface, BLACK, (x - 15, y - 10), 4)
    pygame.draw.circle(surface, WHITE, (x + 15, y - 10), 10)
    pygame.draw.circle(surface, BLACK, (x + 15, y - 10), 4)

    # 3. Beak
    pygame.draw.polygon(surface, ORANGE, [(x - 5, y + 5), (x + 5, y + 5), (x, y + 20)])

    # 4. Wings (The important part!)
    # Note: User's Left is Screen Right (Mirror), but usually users intuit 'My Left Arm' = 'Left Wing on Screen'
    # Let's map strict Left-to-Left for clarity.

    left_wrist_height = max(0.2, min(1.2, left_wrist_height))
    left_wrist_height = (left_wrist_height - 0.7) * 2
    left_wrist_x = left_wrist_height * 20
    left_wrist_y = left_wrist_height * 80

    right_wrist_height = max(0.2, min(1.2, right_wrist_height))
    right_wrist_height = (right_wrist_height - 0.7) * 2
    right_wrist_x = right_wrist_height * 20
    right_wrist_y = right_wrist_height * 80

    #left wing
    points = [(x - 100 - left_wrist_x, y + left_wrist_y), (x - 38, y + 18), (x - 38, y - 18)]
    pygame.draw.polygon(surface, ORANGE, points)
    pygame.draw.polygon(surface, BLACK, points, 3)  # Outline

    #right wing
    points = [(x + 100 + right_wrist_x, y + right_wrist_y), (x + 38, y + 18), (x + 38, y - 18)]
    pygame.draw.polygon(surface, ORANGE, points)
    pygame.draw.polygon(surface, BLACK, points, 3)  # Outline

def ghost_wings(surface, x, y, left_wrist_height):
    transparent_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    FILL = (200, 200, 200, 100)
    OUTLINE = (50, 50, 50, 150)

    left_wrist_height = max(0.2, min(1.2, left_wrist_height))
    left_wrist_height = (left_wrist_height - 0.7) * 2
    left_wrist_x = left_wrist_height * 20
    left_wrist_y = left_wrist_height * 80
    print("ghost")

    # left wing
    points = [(x - 100 - left_wrist_x, y + left_wrist_y), (x - 38, y + 18), (x - 38, y - 18)]
    pygame.draw.polygon(transparent_layer, FILL, points)
    pygame.draw.polygon(transparent_layer, OUTLINE, points, 3)

    # right wing
    points = [(x + 100 + left_wrist_x, y + left_wrist_x), (x + 38, y + 18), (x + 38, y - 18)]
    pygame.draw.polygon(transparent_layer, FILL, points)
    pygame.draw.polygon(transparent_layer, OUTLINE, points, 3)  # Outline

    surface.blit(transparent_layer, (0, 0))

# --- MAIN LOOP ---
clock = pygame.time.Clock()
running = True
previous_bird_y = SCREEN_HEIGHT // 2
debug_trigger = False
feedback_end_time = 0

# UI Rectangles
start_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 550, 200, 60)
guide_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 620, 200, 50)
back_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 620, 200, 60)
reps_minus_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 350, 50, 50)
reps_plus_rect = pygame.Rect(SCREEN_WIDTH // 2 + 100, 350, 50, 50)
sets_minus_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 450, 50, 50)
sets_plus_rect = pygame.Rect(SCREEN_WIDTH // 2 + 100, 450, 50, 50)
play_again_rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, 500, 200, 60)
quit_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, 500, 200, 60)

print("--- VERSION 2 (VIDEO + DYNAMIC BIRD + AUDIO) STARTED ---")

while running:
    current_time = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # MENU
        if game_state == 'MENU':
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn_rect.collidepoint(event.pos):
                    game_state = 'PLAYING'
                    reps_at_start_of_set = mt.lateral_raise_count
                    current_set = 1

                if guide_btn_rect.collidepoint(event.pos):
                    game_state = 'GUIDE'
                    if os.path.exists(video_path):
                        cap_guide = cv2.VideoCapture(video_path)
                    else:
                        cap_guide = None

                    # Load and play audio
                    if os.path.exists(audio_path):
                        try:
                            tutorial_audio = pygame.mixer.Sound(audio_path)
                            tutorial_audio.play()
                        except Exception as e:
                            print(f"Audio Error: {e}")
                            tutorial_audio = None
                    else:
                        print("Audio file not found: tutorial_audio.wav")

                if reps_minus_rect.collidepoint(event.pos) and target_reps > 1: target_reps -= 1
                if reps_plus_rect.collidepoint(event.pos): target_reps += 1
                if sets_minus_rect.collidepoint(event.pos) and target_sets > 1: target_sets -= 1
                if sets_plus_rect.collidepoint(event.pos): target_sets += 1

        # GUIDE (Video)
        elif game_state == 'GUIDE':
            if event.type == pygame.MOUSEBUTTONDOWN and back_btn_rect.collidepoint(event.pos):
                game_state = 'MENU'
                if cap_guide:
                    cap_guide.release()
                    cap_guide = None
                # Stop audio when leaving guide
                if tutorial_audio:
                    tutorial_audio.stop()
                    tutorial_audio = None

        # VICTORY
        elif game_state == 'VICTORY':
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_rect.collidepoint(event.pos): game_state = 'MENU'
                if quit_rect.collidepoint(event.pos): running = False

        # PLAYING
        if game_state == 'PLAYING':
            # Spacebar test key
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                mt.left_arm_up = True  # Simulate Up
                mt.right_arm_up = True
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                mt.left_arm_up = False
                mt.right_arm_up = False

    # --- DRAWING ---
    screen.fill(SKY_BLUE)

    if game_state == 'MENU':
        title = font_big.render("Bird Game (Version 2)", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))
        draw_text_centered("Setup Your Workout", font_ui, DARK_GRAY, 250)

        # Settings
        draw_text_centered(f"Reps per Set: {target_reps}", font_ui, BLACK, 310)
        draw_button(reps_minus_rect, "-", reps_minus_rect.collidepoint(mouse_pos))
        draw_button(reps_plus_rect, "+", reps_plus_rect.collidepoint(mouse_pos))

        draw_text_centered(f"Total Sets: {target_sets}", font_ui, BLACK, 410)
        draw_button(sets_minus_rect, "-", sets_minus_rect.collidepoint(mouse_pos))
        draw_button(sets_plus_rect, "+", sets_plus_rect.collidepoint(mouse_pos))

        draw_button(start_btn_rect, "START GAME", start_btn_rect.collidepoint(mouse_pos))
        draw_button(guide_btn_rect, "WATCH TUTORIAL", guide_btn_rect.collidepoint(mouse_pos), color=GRAY)

    elif game_state == 'GUIDE':
        if cap_guide and cap_guide.isOpened():
            ret, frame = cap_guide.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.transpose(frame, (1, 0, 2))  # swap width & height
                frame = pygame.surfarray.make_surface(frame)
                frame = pygame.transform.scale(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
                screen.blit(frame, (0, 0))
            else:
                # Loop video
                cap_guide.set(cv2.CAP_PROP_POS_FRAMES, 0)
                # Loop audio if it finished
                if tutorial_audio and not pygame.mixer.get_busy():
                    tutorial_audio.play()
        else:
            screen.fill(BLACK)
            draw_text_centered("Video not found: tutorial.mp4", font_msg, RED, 300)

        draw_button(back_btn_rect, "BACK", back_btn_rect.collidepoint(mouse_pos))

    elif game_state == 'PLAYING':
        # Logic
        current_reps_done = mt.lateral_raise_count - reps_at_start_of_set

        if current_reps_done >= target_reps:
            if current_set < target_sets:
                game_state = 'REST'
                rest_end_time = current_time + REST_DURATION
            else:
                game_state = 'VICTORY'

        # Feedback
        if mt.incorrect_form_detected: feedback_end_time = current_time + FEEDBACK_DURATION
        show_red_alert = mt.incorrect_form_detected

        # *** DYNAMIC BIRD ***
        # We pass the real-time arm state from motion_tracking
        draw_dynamic_bird(
            screen,
            SCREEN_WIDTH // 2,
            BIRD_Y,
            mt.left_arm_up,
            mt.right_arm_up,
            mt.left_wrist_height,
            mt.right_wrist_height
        )

        # UI Stats
        pygame.draw.rect(screen, WHITE, (20, 20, 280, 110), border_radius=10)
        pygame.draw.rect(screen, BLACK, (20, 20, 280, 110), 2, border_radius=10)
        screen.blit(font_ui.render(f"Set: {current_set} / {target_sets}", True, BLACK), (35, 30))
        screen.blit(font_ui.render(f"Reps: {current_reps_done} / {target_reps}", True, BLACK), (35, 65))
        screen.blit(font_small.render(f"Total Reps: {mt.lateral_raise_count}", True, DARK_GRAY), (35, 100))

        # Wrong Form Alert
        if show_red_alert:
            pygame.draw.rect(screen, RED, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 15)
            warn_bg = pygame.Surface((400, 80))
            warn_bg.fill(WHITE)
            warn_bg.set_alpha(200)
            screen.blit(warn_bg, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 40))
            screen.blit(font_msg.render("WRONG FORM!", True, RED), (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 20))
            # Text explanation
            screen.blit(font_ui.render("Raise BOTH arms evenly!", True, RED),
                        (SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 + 30))
            ghost_wings(
                screen,
                SCREEN_WIDTH // 2,
                BIRD_Y,
                mt.left_wrist_height,
            )

    elif game_state == 'REST':
        remaining = rest_end_time - current_time
        if remaining <= 0:
            game_state = 'PLAYING'
            current_set += 1
            reps_at_start_of_set = mt.lateral_raise_count

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(WHITE)
        screen.blit(overlay, (0, 0))
        draw_text_centered("SET COMPLETE!", font_big, GREEN, 200)
        draw_text_centered("Next set starts in:", font_ui, BLACK, 300)
        draw_text_centered(str(int(remaining / 1000) + 1), font_big, RED, 360)

    elif game_state == 'VICTORY':
        screen.fill(GREEN)
        draw_text_centered("WORKOUT COMPLETE!", font_big, WHITE, 200)
        draw_text_centered(f"You finished {target_sets} sets.", font_ui, WHITE, 300)
        draw_button(play_again_rect, "PLAY AGAIN", play_again_rect.collidepoint(mouse_pos))
        draw_button(quit_rect, "QUIT", quit_rect.collidepoint(mouse_pos), color=RED)

    pygame.display.flip()
    clock.tick(30)

# Cleanup
if cap_guide:
    cap_guide.release()
if tutorial_audio:
    tutorial_audio.stop()
pygame.quit()
sys.exit()