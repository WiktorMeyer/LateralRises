import pygame
import threading
import sys
import os

# --- IMPORT TRACKING SCRIPT ---
import motion_tracking as mt

# --- CONFIGURATION ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
ANIMATION_SPEED = 0.25
FEEDBACK_DURATION = 2000  # GIF lingers for 2 seconds
REST_DURATION = 10000  # 10 Seconds Rest Time

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
pygame.display.set_caption("Group 6: Gamified Strength Trainer")

# Fonts
font_ui = pygame.font.SysFont("Arial", 28, bold=True)
font_big = pygame.font.SysFont("Arial", 60, bold=True)
font_msg = pygame.font.SysFont("Arial", 40, bold=True)
font_small = pygame.font.SysFont("Arial", 20)

# --- GLOBAL VARIABLES FOR GAME STATE ---
# Game States: 'MENU', 'PLAYING', 'REST', 'VICTORY'
game_state = 'MENU'

# User Settings (Defaults)
target_reps = 10
target_sets = 3

# Progress Tracking
current_set = 1
reps_at_start_of_set = 0
rest_end_time = 0  # For the countdown

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

# 2. Load Feedback Animation
feedback_frames = []
for i in range(10):
    filename = f"frame_{str(i).zfill(2)}_delay-0.2s.png"
    if os.path.exists(filename):
        try:
            img = pygame.image.load(filename)
            img = pygame.transform.scale(img, (300, 200))
            feedback_frames.append(img)
        except Exception as e:
            print(f"Error loading {filename}: {e}")


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


def draw_button(rect, text, hover=False, color=BUTTON_COLOR):
    draw_col = BUTTON_HOVER if hover else color
    pygame.draw.rect(screen, draw_col, rect, border_radius=10)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=10)
    text_surf = font_ui.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)


# --- MAIN LOOP ---
clock = pygame.time.Clock()
running = True
previous_bird_y = SCREEN_HEIGHT // 2
debug_trigger = False
feedback_end_time = 0

# UI Rectangles
start_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 550, 200, 60)
reps_minus_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 350, 50, 50)
reps_plus_rect = pygame.Rect(SCREEN_WIDTH // 2 + 100, 350, 50, 50)
sets_minus_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 450, 50, 50)
sets_plus_rect = pygame.Rect(SCREEN_WIDTH // 2 + 100, 450, 50, 50)

# Victory Buttons
play_again_rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, 500, 200, 60)
quit_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, 500, 200, 60)

print("--- GAME STARTED ---")

while running:
    current_time = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()

    # --- EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # MENU INTERACTIONS
        if game_state == 'MENU':
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn_rect.collidepoint(event.pos):
                    # START GAME
                    game_state = 'PLAYING'
                    reps_at_start_of_set = mt.lateral_raise_count
                    current_set = 1

                # Adjust Reps
                if reps_minus_rect.collidepoint(event.pos) and target_reps > 1:
                    target_reps -= 1
                if reps_plus_rect.collidepoint(event.pos):
                    target_reps += 1

                # Adjust Sets
                if sets_minus_rect.collidepoint(event.pos) and target_sets > 1:
                    target_sets -= 1
                if sets_plus_rect.collidepoint(event.pos):
                    target_sets += 1

        # VICTORY INTERACTIONS
        elif game_state == 'VICTORY':
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_rect.collidepoint(event.pos):
                    game_state = 'MENU'
                if quit_rect.collidepoint(event.pos):
                    running = False

        # PLAYING DEBUG
        if game_state == 'PLAYING':
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                feedback_end_time = current_time + FEEDBACK_DURATION
                debug_trigger = True
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                debug_trigger = False

    # --- LOGIC & DRAWING ---
    screen.fill(SKY_BLUE)

    if game_state == 'MENU':
        # Title
        title = font_big.render("Gamified Strength Trainer", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        # Settings
        instr = font_ui.render("Configure Your Workout:", True, DARK_GRAY)
        screen.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2, 250))

        # Reps
        reps_label = font_ui.render(f"Reps per Set: {target_reps}", True, BLACK)
        screen.blit(reps_label, (SCREEN_WIDTH // 2 - reps_label.get_width() // 2, 310))
        draw_button(reps_minus_rect, "-", reps_minus_rect.collidepoint(mouse_pos))
        draw_button(reps_plus_rect, "+", reps_plus_rect.collidepoint(mouse_pos))

        # Sets
        sets_label = font_ui.render(f"Total Sets: {target_sets}", True, BLACK)
        screen.blit(sets_label, (SCREEN_WIDTH // 2 - sets_label.get_width() // 2, 410))
        draw_button(sets_minus_rect, "-", sets_minus_rect.collidepoint(mouse_pos))
        draw_button(sets_plus_rect, "+", sets_plus_rect.collidepoint(mouse_pos))

        # Start
        draw_button(start_btn_rect, "START GAME", start_btn_rect.collidepoint(mouse_pos))

    elif game_state == 'PLAYING':
        # Logic: Current reps in this set
        current_reps_done = mt.lateral_raise_count - reps_at_start_of_set

        # Set Completion
        if current_reps_done >= target_reps:
            if current_set < target_sets:
                game_state = 'REST'
                rest_end_time = current_time + REST_DURATION  # Start 10s Timer
            else:
                game_state = 'VICTORY'

        # --- GAME VISUALS ---
        wrist_height = get_normalized_wrist_height()
        target_bird_y = int(wrist_height * (SCREEN_HEIGHT - 100)) + 50
        current_bird_y = previous_bird_y + (target_bird_y - previous_bird_y) * 0.2

        if current_bird_y < previous_bird_y - 1:
            is_flying_up = True
        else:
            is_flying_up = False
        previous_bird_y = current_bird_y

        # Feedback Logic
        if mt.incorrect_form_detected:
            feedback_end_time = current_time + FEEDBACK_DURATION
        show_gif = current_time < feedback_end_time
        show_red_alert = mt.incorrect_form_detected or debug_trigger

        # Draw Elements
        pygame.draw.line(screen, GREEN, (0, 100), (SCREEN_WIDTH, 100), 5)
        goal_label = font_ui.render("GOAL HEIGHT", True, GREEN)
        screen.blit(goal_label, (10, 70))

        if bird_up_img and bird_down_img:
            if is_flying_up:
                screen.blit(bird_up_img, (SCREEN_WIDTH // 2 - 40, int(current_bird_y) - 30))
            else:
                screen.blit(bird_down_img, (SCREEN_WIDTH // 2 - 40, int(current_bird_y) - 30))
        else:
            pygame.draw.circle(screen, (255, 215, 0), (SCREEN_WIDTH // 2, int(current_bird_y)), 30)

        # UI Stats
        score_box_w, score_box_h = 280, 110
        pygame.draw.rect(screen, WHITE, (20, 20, score_box_w, score_box_h), border_radius=10)
        pygame.draw.rect(screen, BLACK, (20, 20, score_box_w, score_box_h), 2, border_radius=10)

        set_text = font_ui.render(f"Set: {current_set} / {target_sets}", True, BLACK)
        reps_text = font_ui.render(f"Reps: {current_reps_done} / {target_reps}", True, BLACK)
        total_score_text = font_small.render(f"Total Score: {mt.lateral_raise_count * 100}", True, DARK_GRAY)

        screen.blit(set_text, (35, 30))
        screen.blit(reps_text, (35, 65))
        screen.blit(total_score_text, (35, 100))

        # Feedback
        if show_red_alert:
            pygame.draw.rect(screen, RED, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 10)
            warn_surf = font_msg.render("WRONG FORM!", True, RED)
            screen.blit(warn_surf, (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2))

        if show_gif:
            anim_x, anim_y = 20, SCREEN_HEIGHT - 220
            pygame.draw.rect(screen, WHITE, (anim_x - 5, anim_y - 5, 310, 210))
            if len(feedback_frames) > 0:
                frame_index = (current_time // (ANIMATION_SPEED * 1000)) % len(feedback_frames)
                screen.blit(feedback_frames[int(frame_index)], (anim_x, anim_y))
            else:
                pygame.draw.rect(screen, RED, (anim_x, anim_y, 300, 200), 2)
                err_text = font_ui.render("No Images", True, RED)
                screen.blit(err_text, (anim_x + 50, anim_y + 90))

    elif game_state == 'REST':
        # Countdown Logic
        remaining_time = rest_end_time - current_time
        if remaining_time <= 0:
            # Time's up -> Go to Next Set
            game_state = 'PLAYING'
            current_set += 1
            reps_at_start_of_set = mt.lateral_raise_count

        # Display Rest Screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(WHITE)
        screen.blit(overlay, (0, 0))

        msg1 = font_big.render("SET COMPLETE!", True, GREEN)
        msg2 = font_ui.render(f"Next set starts in:", True, BLACK)

        # Big Countdown Timer
        seconds_left = int(remaining_time / 1000) + 1
        timer_surf = font_big.render(str(seconds_left), True, RED)

        screen.blit(msg1, (SCREEN_WIDTH // 2 - msg1.get_width() // 2, 200))
        screen.blit(msg2, (SCREEN_WIDTH // 2 - msg2.get_width() // 2, 300))
        screen.blit(timer_surf, (SCREEN_WIDTH // 2 - timer_surf.get_width() // 2, 350))

    elif game_state == 'VICTORY':
        screen.fill(GREEN)
        msg1 = font_big.render("WORKOUT COMPLETE!", True, WHITE)
        msg2 = font_ui.render(f"Great job! You finished {target_sets} sets.", True, WHITE)
        msg3 = font_msg.render(f"Final Score: {mt.lateral_raise_count * 100}", True, WHITE)

        screen.blit(msg1, (SCREEN_WIDTH // 2 - msg1.get_width() // 2, 200))
        screen.blit(msg2, (SCREEN_WIDTH // 2 - msg2.get_width() // 2, 300))
        screen.blit(msg3, (SCREEN_WIDTH // 2 - msg3.get_width() // 2, 400))

        # End Buttons
        draw_button(play_again_rect, "PLAY AGAIN", play_again_rect.collidepoint(mouse_pos))
        draw_button(quit_rect, "QUIT", quit_rect.collidepoint(mouse_pos), color=RED)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()