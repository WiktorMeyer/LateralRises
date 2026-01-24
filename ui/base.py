import pygame
from config import *



class Button:
    def __init__(self, rect, text, color=BUTTON_COLOR):
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