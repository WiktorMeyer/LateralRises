import pygame

pygame.init()
pygame.font.init()

#--- CONFIGURATION ---

# INITIALIZATION
#window size
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
WINDOW_NAME = "Group 6: Bird Game (Final Version)"

# BEFORE-GAME MENU
MENU_TITLE = "Bird Game (Final Version)"
INSTRUCTIONS = [
            "1. Stand back so your upper body is visible to the camera.",
            "2. Hold weights (preferably dumbbells) in your hands.",
            "3. Raise your arms to the side (Lateral Raises).",
            "4. Watch the Bird overlay track your form in real-time.",
            "5. Keep arms straight and synchronized! Don't let one lag behind.",
            "6. If lines turn RED or you see a warning, correct your form!",
            "7. Complete the target reps to finish a set."
        ]

# GAME
#duration of wrong form feedback
FEEDBACK_DURATION = 3000

#rest (wait period) between sets
REST_DURATION = 5000

#default reps and sets
DEFAULT_REPS = 10
DEFAULT_SETS = 3

#size of the camera feed
CAM_W, CAM_H = 320, 240

#GAME-AESTHETIC
# colors
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

# fonts
font_ui = pygame.font.SysFont("Arial", 28, bold=True)
font_big = pygame.font.SysFont("Arial", 60, bold=True)
font_msg = pygame.font.SysFont("Arial", 40, bold=True)
font_small = pygame.font.SysFont("Arial", 22)