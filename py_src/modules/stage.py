import pygame
from libs.utils import point_distance
from libs.assets import Assets
from modules.dog import Dog
from modules.duck import Duck
from modules.hud import Hud
from libs.random_generators.LinearCongruentialGenerator import LinearCongruentialGenerator
rng = LinearCongruentialGenerator()

MAX_X = 800
MAX_Y = 600

DUCK_POINTS_ORIGIN = (MAX_X / 2, MAX_Y)
DOG_POINTS = {
    'DOWN': (MAX_X / 2, MAX_Y),
    'UP': (MAX_X / 2, MAX_Y - 230),
    'SNIFF_START': (0, MAX_Y - 130),
    'SNIFF_END': (MAX_X / 2, MAX_Y - 130)
}
HUD_LOCATIONS = {
  'SCORE': (MAX_X - 10, 10),
    'LIVES': (10, 42),
    'CREDITS': (10, 74),
  'WAVE_STATUS': (MAX_X - 11, MAX_Y - 30),
  'LEVEL_CREATOR_LINK': (MAX_X - 11, MAX_Y - 10),
  'FULL_SCREEN_LINK': (MAX_X - 130, MAX_Y - 10),
  'PAUSE_LINK': (MAX_X - 318, MAX_Y - 10),
  'MUTE_LINK': (MAX_X - 236, MAX_Y - 10),
  'GAME_STATUS': (MAX_X / 2, MAX_Y * 0.45),
    'GAME_OVER_PROMPT': (MAX_X / 2, MAX_Y * 0.57),
  'REPLAY_BUTTON': (MAX_X / 2, MAX_Y * 0.56),
  'BULLET_STATUS': (10, 10),
  'DEAD_DUCK_STATUS': (10, MAX_Y * 0.91),
  'MISSED_DUCK_STATUS': (10, MAX_Y * 0.95)
}

FLASH_MS = 60

class Stage:
    def __init__(self, opts):
        self.locked = False
        self.ducks = []
        self.dog = Dog({
            'downPoint': DOG_POINTS['DOWN'],
            'upPoint': DOG_POINTS['UP']
        })
        self.dog.visible = False
        
        self.flash_screen_visible = False
        self.flash_screen_timer = 0
        self.flash_surface = pygame.Surface((MAX_X, MAX_Y))
        self.flash_surface.fill((255, 255, 255))
        
        self.hud = Hud()
        
        self.background_texture = Assets.get_texture('scene/back/0.png')
        self.tree_texture = Assets.get_texture('scene/tree/0.png')
        
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.dog_behind_bg = False

    @staticmethod
    def score_box_location(): return HUD_LOCATIONS['SCORE']
    @staticmethod
    def lives_box_location(): return HUD_LOCATIONS['LIVES']
    @staticmethod
    def credits_box_location(): return HUD_LOCATIONS['CREDITS']
    @staticmethod
    def wave_status_box_location(): return HUD_LOCATIONS['WAVE_STATUS']
    @staticmethod
    def game_status_box_location(): return HUD_LOCATIONS['GAME_STATUS']
    @staticmethod
    def game_over_prompt_location(): return HUD_LOCATIONS['GAME_OVER_PROMPT']
    @staticmethod
    def pause_link_box_location(): return HUD_LOCATIONS['PAUSE_LINK']
    @staticmethod
    def mute_link_box_location(): return HUD_LOCATIONS['MUTE_LINK']
    @staticmethod
    def fullscreen_link_box_location(): return HUD_LOCATIONS['FULL_SCREEN_LINK']
    @staticmethod
    def level_creator_link_box_location(): return HUD_LOCATIONS['LEVEL_CREATOR_LINK']
    @staticmethod
    def replay_button_location(): return HUD_LOCATIONS['REPLAY_BUTTON']
    @staticmethod
    def bullet_status_box_location(): return HUD_LOCATIONS['BULLET_STATUS']
    @staticmethod
    def dead_duck_status_box_location(): return HUD_LOCATIONS['DEAD_DUCK_STATUS']
    @staticmethod
    def missed_duck_status_box_location(): return HUD_LOCATIONS['MISSED_DUCK_STATUS']

    def pause(self):
        self.dog.timeline.pause()
        for duck in self.ducks:
            duck.timeline.pause()

    def resume(self):
        self.dog.timeline.play()
        for duck in self.ducks:
            duck.timeline.play()

    def scale_to_window(self, win_width, win_height):
        self.scale_x = win_width / MAX_X
        self.scale_y = win_height / MAX_Y

    def pre_level_animation(self, on_complete):
        self.clean_up_ducks()
        self.dog_behind_bg = False
        sniff_opts = {
            'startPoint': DOG_POINTS['SNIFF_START'],
            'endPoint': DOG_POINTS['SNIFF_END']
        }
        
        def find_complete():
            self.dog_behind_bg = True
            if on_complete:
                on_complete()
                
        find_opts = {
            'onComplete': find_complete
        }
        self.dog.sniff(sniff_opts).find(find_opts)

    def add_ducks(self, num_ducks, speed):
        for i in range(num_ducks):
            duck_color = 'red' if i % 2 == 0 else 'black'
            new_duck = Duck({
                'colorProfile': duck_color,
                'maxX': MAX_X,
                'maxY': MAX_Y
            })
            new_duck.x = DUCK_POINTS_ORIGIN[0]
            new_duck.y = DUCK_POINTS_ORIGIN[1]
            new_duck.random_flight({'speed': speed})
            self.ducks.append(new_duck)

    def get_scaled_click_location(self, click_point):
        return (click_point[0] / self.scale_x, click_point[1] / self.scale_y)

    def shots_fired(self, click_point, radius):
        self.flash_screen_visible = True
        self.flash_screen_timer = FLASH_MS / 1000.0
        
        scaled_point = self.get_scaled_click_location(click_point)
        ducks_shot = 0
        for duck in self.ducks:
            if duck.alive and point_distance((duck.x, duck.y), scaled_point) < radius:
                ducks_shot += 1
                duck.shot()
                
                def on_dog_retrieve():
                    if not self.is_locked():
                        self.dog.retrieve()
                duck.timeline.call(on_dog_retrieve)
        return ducks_shot

    def in_range(self, val, min_val, max_val):
        return min_val <= val <= max_val

    def clicked_replay(self, click_point):
        return point_distance(self.get_scaled_click_location(click_point), HUD_LOCATIONS['REPLAY_BUTTON']) < 200

    def clicked_level_creator_link(self, click_point):
        sp = self.get_scaled_click_location(click_point)
        loc = HUD_LOCATIONS['LEVEL_CREATOR_LINK']
        return self.in_range(sp[0], loc[0] - 110, loc[0]) and self.in_range(sp[1], loc[1] - 30, loc[1] + 10)

    def clicked_pause_link(self, click_point):
        sp = self.get_scaled_click_location(click_point)
        loc = HUD_LOCATIONS['PAUSE_LINK']
        return self.in_range(sp[0], loc[0] - 110, loc[0]) and self.in_range(sp[1], loc[1] - 30, loc[1] + 10)

    def clicked_fullscreen_link(self, click_point):
        sp = self.get_scaled_click_location(click_point)
        loc = HUD_LOCATIONS['FULL_SCREEN_LINK']
        return self.in_range(sp[0], loc[0] - 110, loc[0]) and self.in_range(sp[1], loc[1] - 30, loc[1] + 10)

    def clicked_mute_link(self, click_point):
        sp = self.get_scaled_click_location(click_point)
        loc = HUD_LOCATIONS['MUTE_LINK']
        return self.in_range(sp[0], loc[0] - 110, loc[0]) and self.in_range(sp[1], loc[1] - 30, loc[1] + 10)

    def fly_away(self, on_complete):
        self.dog.stop_and_clear_timeline()
        self.dog.laugh()
        self.lock()
        
        active_ducks = [d for d in self.ducks if d.alive]
        if not active_ducks:
            self.clean_up_ducks()
            self.unlock()
            if on_complete: on_complete()
            return

        completed_count = [0]
        
        def check_complete():
            completed_count[0] += 1
            if completed_count[0] == len(active_ducks):
                self.clean_up_ducks()
                self.unlock()
                if on_complete: on_complete()
        
        for duck in active_ducks:
            duck.stop_and_clear_timeline()
            duck.fly_to({
                'point': (MAX_X / 2, -500),
                'onComplete': check_complete
            })

    def clean_up_ducks(self):
        self.ducks = []

    def ducks_alive(self):
        return any(duck.alive for duck in self.ducks)

    def ducks_active(self):
        return any(duck.is_active() for duck in self.ducks)

    def dog_active(self):
        return self.dog.is_active()

    def is_active(self):
        return self.dog_active() or self.ducks_alive() or self.ducks_active()

    def lock(self): self.locked = True
    def unlock(self): self.locked = False
    def is_locked(self): return self.locked

    def update(self, dt):
        if self.flash_screen_visible:
            self.flash_screen_timer -= dt
            if self.flash_screen_timer <= 0:
                self.flash_screen_visible = False
                
        self.dog.update(dt)
        for duck in self.ducks:
            duck.update(dt)

    def _scale_image(self, image):
        """Scale an image based on current window scale factors."""
        if self.scale_x == 1.0 and self.scale_y == 1.0:
            return image
        new_width = max(1, int(image.get_width() * self.scale_x))
        new_height = max(1, int(image.get_height() * self.scale_y))
        return pygame.transform.scale(image, (new_width, new_height))
    
    def _scale_rect(self, rect):
        """Scale a rect position/size based on current window scale factors."""
        return pygame.Rect(
            int(rect.x * self.scale_x),
            int(rect.y * self.scale_y),
            max(1, int(rect.width * self.scale_x)),
            max(1, int(rect.height * self.scale_y))
        )

    def draw(self, surface):
        # 1. First layer: Ducks (they fall behind background grass/tree)
        for duck in self.ducks:
            if duck.visible:
                scaled_image = self._scale_image(duck.image)
                scaled_rect = self._scale_rect(duck.rect)
                surface.blit(scaled_image, scaled_rect)
        
        # 2. Second layer: Dog (if behind bg, like when retrieving ducks or laughing)
        if self.dog_behind_bg and self.dog.visible:
            scaled_dog = self._scale_image(self.dog.image)
            scaled_dog_rect = self._scale_rect(self.dog.rect)
            surface.blit(scaled_dog, scaled_dog_rect)

        # 3. Third layer: Tree
        if self.tree_texture:
            scaled_tree = self._scale_image(self.tree_texture)
            tree_pos = (int(100 * self.scale_x), int(237 * self.scale_y))
            surface.blit(scaled_tree, tree_pos)
            
        # 4. Fourth layer: Background (Foreground grass with transparent sky)
        if self.background_texture:
            scaled_bg = self._scale_image(self.background_texture)
            surface.blit(scaled_bg, (0, 0))
            
        # 5. Fifth layer: Dog (if NOT behind bg, like during intro sniffing)
        if not self.dog_behind_bg and self.dog.visible:
            scaled_dog = self._scale_image(self.dog.image)
            scaled_dog_rect = self._scale_rect(self.dog.rect)
            surface.blit(scaled_dog, scaled_dog_rect)

        # 6. Sixth layer: Flash Screen and HUD
        if self.flash_screen_visible:
            scaled_flash = pygame.transform.scale(self.flash_surface, 
                (int(self.flash_surface.get_width() * self.scale_x),
                 int(self.flash_surface.get_height() * self.scale_y)))
            surface.blit(scaled_flash, (0, 0))
            
        self.hud.draw(surface, self.scale_x, self.scale_y)
