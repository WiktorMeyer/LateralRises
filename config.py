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