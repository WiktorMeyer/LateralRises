import sys
import os
import cv2
import numpy as np

# import other files
import config
from config import *
from ui.base import Button, ProgressBar
from core.motion_tracker import MotionTracker


class GameState:
    def __init__(self):
        self.bird_y = SCREEN_HEIGHT // 2
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.game_state = 'MENU'
        self.target_reps = config.DEFAULT_REPS
        self.target_sets = config.DEFAULT_SETS
        self.current_set = 1
        self.reps_at_start_of_set = 0
        self.rest_end_time = 0
        self.seen_tutorial = False
        self.show_tutorial_popup = False
        #feedback
        self.feedback_end_time = pygame.time.get_ticks()
        self.show_red_alert = False
        # Paths relative to game_state.py
        self.video_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'video tutorial.mp4')
        self.audio_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'tutorial_audio.wav')
        #buttons
        self.buttons = self.create_buttons()

    def draw_text_centered(self, text, font, color, y_offset):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
        self.screen.blit(surf, rect)

    def create_buttons(self):
        return{
            # UI Buttons
            'start': Button(pygame.Rect(SCREEN_WIDTH // 2 - 100, 550, 200, 60), "START GAME"),
            'guide': Button(pygame.Rect(SCREEN_WIDTH // 2 + 20, 620, 200, 50), "WATCH TUTORIAL", color=GREEN),
            'text_guide': Button(pygame.Rect(SCREEN_WIDTH // 2 - 220, 620, 200, 50), "READ TUTORIAL", color=GREEN),
            'back': Button(pygame.Rect(SCREEN_WIDTH // 2 - 100, 620, 200, 60), "BACK", color=RED),
            'reps_minus': Button(pygame.Rect(SCREEN_WIDTH // 2 - 150, 350, 50, 50),"-"),
            'reps_plus': Button(pygame.Rect(SCREEN_WIDTH // 2 + 100, 350, 50, 50), "+"),
            'sets_minus': Button(pygame.Rect(SCREEN_WIDTH // 2 - 150, 450, 50, 50), "-"),
            'sets_plus': Button(pygame.Rect(SCREEN_WIDTH // 2 + 100, 450, 50, 50), "+"),
            'play_again': Button(pygame.Rect(SCREEN_WIDTH // 2 - 220, 500, 200, 60), "PLAY AGAIN"),
            'quit': Button(pygame.Rect(SCREEN_WIDTH // 2 + 20, 500, 200, 60), "QUIT", color=RED),
            'popup': Button(pygame.Rect(SCREEN_WIDTH // 2 - 150, 550, 300, 60), "SEE THE TUTORIAL FIRST", color=GRAY)
        }

    # --- NEW: DYNAMIC BIRD DRAWING ---
    def draw_dynamic_bird(self, surface, x, y, left_up, right_up, left_wrist_height, right_wrist_height):
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

    def ghost_wings(self, surface, x, y, left_wrist_height):
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

    def run(self):
        mt = MotionTracker()

        # --- INITIALIZATION ---
        pygame.init()
        pygame.mixer.init()  # Initialize the mixer for audio
        pygame.display.set_caption(config.WINDOW_NAME)

        cap_guide = None
        tutorial_audio = None

        # --- MAIN LOOP ---
        clock = pygame.time.Clock()
        running = True
        previous_bird_y = SCREEN_HEIGHT // 2
        debug_trigger = False

        print("--- VERSION 2 (VIDEO + DYNAMIC BIRD + AUDIO) STARTED ---")

        while running:
            current_time = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # MENU
                if self.game_state == 'MENU':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.buttons['start'].is_clicked(mouse_pos):
                            if self.seen_tutorial:
                                mt.start()
                                self.game_state = 'PLAYING'
                                self.reps_at_start_of_set = mt.lateral_raise_count
                                self.current_set = 1
                            else:
                                self.show_tutorial_popup = True

                        if self.buttons['guide'].is_clicked(mouse_pos):
                            self.game_state = 'GUIDE'
                            if os.path.exists(self.video_path):
                                cap_guide = cv2.VideoCapture(self.video_path)
                            else:
                                cap_guide = None

                            # Load and play audio
                            if os.path.exists(self.audio_path):
                                try:
                                    tutorial_audio = pygame.mixer.Sound(self.audio_path)
                                    tutorial_audio.play()
                                except Exception as e:
                                    print(f"Audio Error: {e}")
                                    tutorial_audio = None
                            else:
                                print("Audio file not found: tutorial_audio.wav")

                        if self.buttons['text_guide'].is_clicked(mouse_pos):
                            self.game_state = 'TEXT_GUIDE'

                        if self.buttons['reps_minus'].is_clicked(mouse_pos) and self.target_reps > 1: self.target_reps -= 1
                        if self.buttons['reps_plus'].is_clicked(mouse_pos): self.target_reps += 1
                        if self.buttons['sets_minus'].is_clicked(mouse_pos) and self.target_sets > 1: self.target_sets -= 1
                        if self.buttons['sets_plus'].is_clicked(mouse_pos): self.target_sets += 1

                # GUIDE (Video)
                elif self.game_state == 'GUIDE':
                    if event.type == pygame.MOUSEBUTTONDOWN and self.buttons['back'].is_clicked(mouse_pos):
                        self.game_state = 'MENU'
                        if cap_guide:
                            cap_guide.release()
                            cap_guide = None
                        # Stop audio when leaving guide
                        if tutorial_audio:
                            tutorial_audio.stop()
                            tutorial_audio = None

                elif self.game_state == 'TEXT_GUIDE':
                    if event.type == pygame.MOUSEBUTTONDOWN and self.buttons['back'].is_clicked(mouse_pos):
                        self.game_state = 'MENU'

                # VICTORY
                elif self.game_state == 'VICTORY':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.buttons['play_again'].is_clicked(mouse_pos): self.game_state = 'MENU'
                        if self.buttons['quit'].is_clicked(mouse_pos): running = False

                # PLAYING
                if self.game_state == 'PLAYING':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.buttons['back'].is_clicked(mouse_pos):
                            self.game_state = 'MENU'
                    # Spacebar test key
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        mt.left_arm_up = True  # Simulate Up
                        mt.right_arm_up = True
                    if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                        mt.left_arm_up = False
                        mt.right_arm_up = False
            self.screen.fill(SKY_BLUE)
            # CAMERA
            if self.game_state == 'PLAYING':
                if mt.latest_visualized_frame is not None:
                    # Get frame from motion_tracking
                    frame = mt.latest_visualized_frame.copy()  # Use copy to avoid modifying original

                    # Convert OpenCV (BGR) to Pygame (RGB)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Rotate 90 degrees counterclockwise and flip to correct orientation
                    frame = np.rot90(frame)

                    # Create Pygame Surface
                    frame_surface = pygame.surfarray.make_surface(frame)

                    # Scale to fit window
                    frame_surface = pygame.transform.scale(frame_surface, (CAM_W, CAM_H))

                    cam_x = 0
                    cam_y = SCREEN_HEIGHT - CAM_H

                    # Draw the camera feed
                    self.screen.blit(frame_surface, (cam_x, cam_y))
                else:
                    # Fallback if camera not ready
                    pygame.draw.rect(self.screen, BLACK, (0, SCREEN_HEIGHT - CAM_H, CAM_W, CAM_H))
                    temp_text = font_small.render("Loading Camera...", True, WHITE)
                    self.screen.blit(temp_text, (10, SCREEN_HEIGHT - CAM_H + 110))

            # --- DRAWING ---

            if self.game_state == 'MENU':
                title = font_big.render(config.MENU_TITLE, True, BLACK)
                self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))
                self.draw_text_centered("Setup Your Workout", font_ui, DARK_GRAY, 250)

                # Settings
                self.draw_text_centered(f"Reps per Set: {self.target_reps}", font_ui, BLACK, 310)

                self.buttons['reps_minus'].draw(self.screen, self.buttons['reps_minus'].rect.collidepoint(mouse_pos))
                self.buttons['reps_plus'].draw(self.screen, self.buttons['reps_plus'].rect.collidepoint(mouse_pos))

                self.draw_text_centered(f"Total Sets: {self.target_sets}", font_ui, BLACK, 410)

                self.buttons['sets_minus'].draw(self.screen, self.buttons['sets_minus'].rect.collidepoint(mouse_pos))
                self.buttons['sets_plus'].draw(self.screen, self.buttons['sets_plus'].rect.collidepoint(mouse_pos))

                self.buttons['start'].draw(self.screen, self.buttons['start'].rect.collidepoint(mouse_pos))
                self.buttons['guide'].draw(self.screen, self.buttons['guide'].rect.collidepoint(mouse_pos))
                self.buttons['text_guide'].draw(self.screen, self.buttons['text_guide'].rect.collidepoint(mouse_pos))

                if self.show_tutorial_popup and not self.seen_tutorial:
                    self.buttons['popup'].draw(self.screen)

            elif self.game_state == 'GUIDE':
                self.seen_tutorial = True
                if cap_guide and cap_guide.isOpened():
                    ret, frame = cap_guide.read()
                    if ret:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame = np.transpose(frame, (1, 0, 2))  # swap width & height
                        frame = pygame.surfarray.make_surface(frame)
                        frame = pygame.transform.scale(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
                        self.screen.blit(frame, (0, 0))
                    else:
                        # Loop video
                        cap_guide.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        # Loop audio if it finished
                        if tutorial_audio and not pygame.mixer.get_busy():
                            tutorial_audio.play()
                else:
                    self.screen.fill(BLACK)
                    self.draw_text_centered("Video not found: tutorial.mp4", font_msg, RED, 300)

                self.buttons['back'].draw(self.screen, self.buttons['back'].rect.collidepoint(mouse_pos))

            elif self.game_state == 'TEXT_GUIDE':
                self.seen_tutorial = True
                overlay = pygame.Surface((850, 500))
                overlay.fill(WHITE)
                overlay.set_alpha(230)
                self.screen.blit(overlay, (75, 100))
                pygame.draw.rect(self.screen, BLACK, (75, 100, 850, 500), 3)

                self.draw_text_centered("HOW TO PLAY", font_big, BLACK, 150)

                y_start = 230
                for line in config.INSTRUCTIONS:
                    self.draw_text_centered(line, font_small, BLACK, y_start)
                    y_start += 50
                self.buttons['back'].draw(self.screen, self.buttons['back'].rect.collidepoint(mouse_pos))


            elif self.game_state == 'PLAYING':

                # Logic

                current_reps_done = mt.lateral_raise_count - self.reps_at_start_of_set

                if current_reps_done >= self.target_reps:

                    if self.current_set < self.target_sets:

                        self.game_state = 'REST'

                        self.rest_end_time = current_time + REST_DURATION

                    else:

                        self.game_state = 'VICTORY'

                # Feedback

                if mt.incorrect_form_detected:
                    self.feedback_end_time = current_time + FEEDBACK_DURATION
                    self.show_red_alert = True
                else:
                    if current_time > self.feedback_end_time:
                        self.show_red_alert = False

                # *** DYNAMIC BIRD ***

                # We pass the real-time arm state from motion_tracking

                self.draw_dynamic_bird(

                    self.screen,

                    SCREEN_WIDTH // 2,

                    self.bird_y,

                    mt.left_arm_up,

                    mt.right_arm_up,

                    mt.left_wrist_height,

                    mt.right_wrist_height

                )

                # UI Stats

                pygame.draw.rect(self.screen, WHITE, (20, 20, 240, 110), border_radius=10)

                pygame.draw.rect(self.screen, BLACK, (20, 20, 240, 110), 2, border_radius=10)

                self.screen.blit(font_ui.render(f"Set: {self.current_set} / {self.target_sets}", True, BLACK), (35, 30))

                self.screen.blit(font_ui.render(f"Reps: {current_reps_done} / {self.target_reps}", True, BLACK), (35, 65))

                self.screen.blit(font_small.render(f"Total Reps: {mt.lateral_raise_count}", True, DARK_GRAY), (35, 100))

                # Progress Bar parameters

                bar_width = 400
                bar_height = 30
                bar_x = SCREEN_WIDTH // 2 - bar_width // 2
                bar_y = 100

                # Background
                progress_bar = ProgressBar((bar_x, bar_y, bar_width, bar_height), GRAY, 15)

                progress = min(current_reps_done / self.target_reps, 1.0)

                if current_reps_done > 0:
                    progress_bar.draw(self.screen, progress)

                # Border
                pygame.draw.rect(self.screen, BLACK, (bar_x, bar_y, bar_width, bar_height), 3, border_radius=0)

                # Progress text

                progress_text = font_small.render(f"PROGRESS: {current_reps_done}/{self.target_reps}", True, BLACK)

                text_rect = progress_text.get_rect(center=(SCREEN_WIDTH // 2, bar_y + bar_height // 2))

                self.screen.blit(progress_text, text_rect)

                #quit button
                self.buttons['back'].draw(self.screen, self.buttons['back'].rect.collidepoint(mouse_pos))

                # Wrong Form Alert
                if self.show_red_alert:
                    pygame.draw.rect(self.screen, RED, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 15)
                    warn_bg = pygame.Surface((400, 80))
                    warn_bg.fill(WHITE)
                    warn_bg.set_alpha(200)
                    self.screen.blit(warn_bg, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 5 - 40))
                    self.screen.blit(font_msg.render("WRONG FORM!", True, RED), (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 5 - 20))
                    # Text explanation
                    self.screen.blit(font_ui.render("Raise BOTH arms evenly!", True, RED),
                                (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 5 + 50 ))
                    self.ghost_wings(
                        self.screen,
                        SCREEN_WIDTH // 2,
                        self.bird_y,
                        mt.left_wrist_height,
                    )

            elif self.game_state == 'REST':
                remaining = self.rest_end_time - current_time
                if remaining <= 0:
                    self.game_state = 'PLAYING'
                    self.current_set += 1
                    self.reps_at_start_of_set = mt.lateral_raise_count

                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.set_alpha(180)
                overlay.fill(WHITE)
                self.screen.blit(overlay, (0, 0))
                self.draw_text_centered("SET COMPLETE!", font_big, GREEN, 200)
                self.draw_text_centered("Next set starts in:", font_ui, BLACK, 300)
                self.draw_text_centered(str(int(remaining / 1000) + 1), font_big, RED, 360)

            elif self.game_state == 'VICTORY':
                self.screen.fill(GREEN)
                self.draw_text_centered("WORKOUT COMPLETE!", font_big, WHITE, 200)
                self.draw_text_centered(f"You finished {self.target_sets} sets.", font_ui, WHITE, 300)
                self.buttons['play_again'].draw(self.screen, self.buttons['play_again'].rect.collidepoint(mouse_pos))
                self.buttons['quit'].draw(self.screen, self.buttons['quit'].rect.collidepoint(mouse_pos))

            pygame.display.flip()
            clock.tick(30)

        # Cleanup
        if cap_guide:
            cap_guide.release()
        if tutorial_audio:
            tutorial_audio.stop()
        pygame.quit()
        sys.exit()