import pygame
import sys
import os

from libs.assets import Assets
from libs.tweening import TweenManager
from modules.sound import sound
from modules.game import Game

def main():
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()

    # Load audio
    sound.init('assets/sounds')

    # Create window
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption("Duck Hunt JS (in Python)")

    # Load assets
    Assets.load('assets/sprites/sprites.json', 'assets/sprites/sprites.png')
    Assets.load('assets/sprites/hearts.json', 'assets/sprites/hearts.png')

    game = Game({'spritesheet': 'assets/sprites/sprites.json'})
    game.load(screen)

    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                if game.stage:
                    game.stage.scale_to_window(event.w, event.h)
            elif event.type == pygame.KEYDOWN:
                game.handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    game.handle_click(event.pos)

        TweenManager.update(dt)
        game.update(dt)

        game.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
