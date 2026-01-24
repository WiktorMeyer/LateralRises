from config import *



class Button:
    def __init__(self, rect, text, color=BUTTON_COLOR, width = 0):
        self.rect = rect
        self.text = text
        self.color = color
        self.hover_color = BUTTON_HOVER

    def draw(self, screen, hover=False):
        draw_col = self.hover_color if hover else self.color

        # Drawing logic
        pygame.draw.rect(screen, draw_col, self.rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=10)

        text_surf = font_ui.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

class ProgressBar:
    def __init__(self, rect, color, border_radius):
        self.bar_x = rect[0]
        self.bar_y = rect[1]
        self.bar_width = rect[2]
        self.bar_height = rect[3]
        self.color = color
        self.border_radius = border_radius

    def draw(self, screen, progress):

        fill_width = int(self.bar_width * progress)
        progress_color = self.color
        if fill_width > 0:
            if progress < 0.5:
                progress_color = ORANGE
            elif progress < 0.8:
                progress_color = YELLOW
            else:
                progress_color = GREEN
        fill_width = int(self.bar_width * progress)
        rect = (self.bar_x, self.bar_y, fill_width, self.bar_height)

        pygame.draw.rect(screen, progress_color, rect, self.border_radius)