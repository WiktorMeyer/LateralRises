import pygame
import threading
import sys
import os
import cv2  # NEW: Needed for video processing
import numpy as np  # NEW: Needed for image rotation

# --- IMPORT TRACKING SCRIPT ---
import motion_tracking as mt

# --- CONFIGURATION ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
ANIMATION_SPEED = 0.25
FEEDBACK_DURATION = 2000
REST_DURATION = 10000

# Colors
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
RED = (220, 20, 60)
GREEN = (34, 139, 34)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)

# --- INITIALIZATION ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Group 6: AR Strength Trainer")

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

# --- ASSET LOADING (Feedback Images) ---
feedback_frames = []
for i in range(10):
    filename = f"frame_{str(i).zfill(2)}_delay-0.2s.png"
    if os.path.exists(filename):
        try:
            img = pygame.image.load(filename)
            img = pygame.transform.scale(img, (300, 200))
            feedback_frames.append(img)
        except Exception:
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


# --- MAIN LOOP ---
clock = pygame.time.Clock()
running = True
debug_trigger = False
feedback_end_time = 0

# UI Rectangles
start_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 550, 200, 60)
guide_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 620, 200, 50)
reps_minus_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 350, 50, 50)
reps_plus_rect = pygame.Rect(SCREEN_WIDTH // 2 + 100, 350, 50, 50)
sets_minus_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 450, 50, 50)
sets_plus_rect = pygame.Rect(SCREEN_WIDTH // 2 + 100, 450, 50, 50)
back_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 600, 200, 60)
play_again_rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, 500, 200, 60)
quit_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, 500, 200, 60)

print("--- APP STARTED ---")

while running:
    current_time = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()

    # --- EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # MENU STATE
        if game_state == 'MENU':
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn_rect.collidepoint(event.pos):
                    game_state = 'PLAYING'
                    reps_at_start_of_set = mt.lateral_raise_count
                    current_set = 1
                if guide_btn_rect.collidepoint(event.pos): game_state = 'GUIDE'
                # Settings
                if reps_minus_rect.collidepoint(event.pos) and target_reps > 1: target_reps -= 1
                if reps_plus_rect.collidepoint(event.pos): target_reps += 1
                if sets_minus_rect.collidepoint(event.pos) and target_sets > 1: target_sets -= 1
                if sets_plus_rect.collidepoint(event.pos): target_sets += 1

        # GUIDE / VICTORY STATES
        elif game_state == 'GUIDE':
            if event.type == pygame.MOUSEBUTTONDOWN and back_btn_rect.collidepoint(event.pos):
                game_state = 'MENU'
        elif game_state == 'VICTORY':
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_rect.collidepoint(event.pos): game_state = 'MENU'
                if quit_rect.collidepoint(event.pos): running = False

        # PLAYING STATE (Debug Key)
        if game_state == 'PLAYING':
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                feedback_end_time = current_time + FEEDBACK_DURATION
                debug_trigger = True
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                debug_trigger = False

    # --- DRAWING ---

    # 1. RENDER CAMERA FEED (Background) if in PLAYING mode
    if game_state == 'PLAYING':
        if mt.latest_visualized_frame is not None:
            # Get frame from motion_tracking
            frame = mt.latest_visualized_frame

            # Convert OpenCV (BGR) to Pygame (RGB)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Pygame surfaces are rotated 90 degrees compared to numpy arrays
            frame = np.rot90(frame)

            # Create Pygame Surface
            frame_surface = pygame.surfarray.make_surface(frame)

            # Scale to fit window
            frame_surface = pygame.transform.scale(frame_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))

            # Draw as background
            screen.blit(frame_surface, (0, 0))
        else:
            # Fallback if camera not ready
            screen.fill(BLACK)
            draw_text_centered("Loading Camera...", font_ui, WHITE, SCREEN_HEIGHT // 2)
    else:
        # Solid background for Menus
        screen.fill(SKY_BLUE)

    # 2. DRAW UI ON TOP
    if game_state == 'MENU':
        title = font_big.render("Gamified Workout Machine", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))
        draw_text_centered("Setup Your Workout", font_ui, DARK_GRAY, 250)

        # Settings UI
        draw_text_centered(f"Reps per Set: {target_reps}", font_ui, BLACK, 310)
        draw_button(reps_minus_rect, "-", reps_minus_rect.collidepoint(mouse_pos))
        draw_button(reps_plus_rect, "+", reps_plus_rect.collidepoint(mouse_pos))

        draw_text_centered(f"Total Sets: {target_sets}", font_ui, BLACK, 410)
        draw_button(sets_minus_rect, "-", sets_minus_rect.collidepoint(mouse_pos))
        draw_button(sets_plus_rect, "+", sets_plus_rect.collidepoint(mouse_pos))

        draw_button(start_btn_rect, "START WORKOUT", start_btn_rect.collidepoint(mouse_pos))
        draw_button(guide_btn_rect, "HOW TO PLAY", guide_btn_rect.collidepoint(mouse_pos), color=GRAY)

    elif game_state == 'GUIDE':
        overlay = pygame.Surface((850, 500))
        overlay.fill(WHITE)
        overlay.set_alpha(230)
        screen.blit(overlay, (75, 100))
        pygame.draw.rect(screen, BLACK, (75, 100, 850, 500), 3)

        draw_text_centered("HOW TO PLAY", font_big, BLACK, 150)
        instructions = [
            "1. Stand back so your full body is visible.",
            "2. You will see a Stickman Overlay on your body.",
            "3. Raise your arms (Lateral Raises).",
            "4. The Stickman tracks your form.",
            "5. If lines turn RED or you see a warning, fix your arms!",
            "6. Complete the target reps to finish a set."
        ]
        y_start = 230
        for line in instructions:
            draw_text_centered(line, font_small, BLACK, y_start)
            y_start += 50
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

        # Feedback Logic
        if mt.incorrect_form_detected: feedback_end_time = current_time + FEEDBACK_DURATION
        show_gif = current_time < feedback_end_time
        show_red_alert = mt.incorrect_form_detected or debug_trigger

        # UI Stats Box (Top Left)
        pygame.draw.rect(screen, WHITE, (20, 20, 280, 110), border_radius=10)
        pygame.draw.rect(screen, BLACK, (20, 20, 280, 110), 2, border_radius=10)
        screen.blit(font_ui.render(f"Set: {current_set} / {target_sets}", True, BLACK), (35, 30))
        screen.blit(font_ui.render(f"Reps: {current_reps_done} / {target_reps}", True, BLACK), (35, 65))
        screen.blit(font_small.render(f"Total Reps: {mt.lateral_raise_count}", True, DARK_GRAY), (35, 100))

        # Feedback Overlays
        if show_red_alert:
            # Red Tint on screen edges
            pygame.draw.rect(screen, RED, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 15)
            warn_bg = pygame.Surface((400, 80))
            warn_bg.fill(WHITE)
            warn_bg.set_alpha(200)
            screen.blit(warn_bg, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 40))
            screen.blit(font_msg.render("WRONG FORM!", True, RED), (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 20))

        if show_gif:
            anim_x, anim_y = 20, SCREEN_HEIGHT - 220
            pygame.draw.rect(screen, WHITE, (anim_x - 5, anim_y - 5, 310, 210))
            if len(feedback_frames) > 0:
                frame_index = (current_time // (ANIMATION_SPEED * 1000)) % len(feedback_frames)
                screen.blit(feedback_frames[int(frame_index)], (anim_x, anim_y))
            else:
                pygame.draw.rect(screen, RED, (anim_x, anim_y, 300, 200), 2)
                screen.blit(font_ui.render("Check Form!", True, RED), (anim_x + 70, anim_y + 90))

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
        draw_text_centered(f"You finished {target_sets} sets of {target_reps} reps.", font_ui, WHITE, 300)
        draw_text_centered(f"Total Reps: {mt.lateral_raise_count}", font_msg, WHITE, 400)

        draw_button(play_again_rect, "PLAY AGAIN", play_again_rect.collidepoint(mouse_pos))
        draw_button(quit_rect, "QUIT", quit_rect.collidepoint(mouse_pos), color=RED)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()