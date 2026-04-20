import pygame
import time
import json
from modules.stage import Stage
from modules.sound import sound

BLUE_SKY_COLOR = (100, 176, 255)
PINK_SKY_COLOR = (251, 180, 212)
SUCCESS_RATIO = 0.6
BOTTOM_LINK_STYLE = {'fontFamily': 'Arial', 'fontSize': '15px', 'fill': 'white'}
DIFFICULTY_ORDER = ('easy', 'normal', 'hard')
MAX_LIVES = 3

class Game:
    def __init__(self, opts):
        self.spritesheet = opts.get('spritesheet')
        self.difficulty = opts.get('difficulty', 'normal')
        self.level_index = 0
        self.max_score = 0
        self.time_paused = 0
        self.is_muted = False
        self.is_paused = False
        self.active_sounds = []
        self.state = 'READY'
        self.is_game_over = False

        self.wave_ending = False
        self.quacking_sound_id = None
        
        with open('data/levels.json', 'r') as f:
            self.levels_data = json.load(f)
        self.set_difficulty(self.difficulty)
        
        self.ducks_missed_val = 0
        self.ducks_shot_val = 0
        self.bullet_val = 0
        self.score_val = 0
        self.lives_val = 3
        self.wave_val = 0
        self.game_status_val = ""
        self.level = None
        self.stage = None
        self.wave_start_time = 0
        self.pause_start_time = 0
        self.ducks_shot_this_wave = 0
        self.is_fullscreen = False
        self.bg_color = BLUE_SKY_COLOR
        self.lives = MAX_LIVES

    def _load_levels_for_difficulty(self, difficulty):
        levels = self.levels_data.get(difficulty)
        if levels is not None:
            return levels

        fallback = self.levels_data.get('normal')
        if fallback is not None:
            return fallback

        return next(iter(self.levels_data.values()), [])

    def set_difficulty(self, difficulty):
        difficulty = (difficulty or 'normal').lower()
        if difficulty not in getattr(self, 'levels_data', {}):
            difficulty = 'normal'

        self.difficulty = difficulty
        if hasattr(self, 'levels_data'):
            self.levels = self._load_levels_for_difficulty(difficulty)
        self.update_difficulty_link()

    def cycle_difficulty(self):
        current_index = DIFFICULTY_ORDER.index(self.difficulty) if self.difficulty in DIFFICULTY_ORDER else 1
        next_index = (current_index + 1) % len(DIFFICULTY_ORDER)
        self.set_difficulty(DIFFICULTY_ORDER[next_index])
        self.restart_game()

    def difficulty_link_text(self):
        return f"difficulty: {self.difficulty} (c)"

    def update_difficulty_link(self):
        stage = getattr(self, 'stage', None)
        if stage and stage.hud and 'levelCreatorLink' in stage.hud._items:
            stage.hud.levelCreatorLink = self.difficulty_link_text()

    def reset_game_state(self):
        self.level_index = 0
        self.max_score = 0
        self.time_paused = 0
        self.is_paused = False
        self.active_sounds = []
        self.state = 'READY'
        self.is_game_over = False
        self.wave_ending = False
        self.quacking_sound_id = None
        self.level = None
        self.stage = None
        self.ducks_missed = 0
        self.ducks_shot = 0
        self.bullets = 0
        self.score = 0
        self.wave = 0
        self.game_status = ''
        self.wave_start_time = 0
        self.pause_start_time = 0
        self.ducks_shot_this_wave = 0
        self.bg_color = BLUE_SKY_COLOR
        self.lives = MAX_LIVES
        sound.mute(self.is_muted)

    def restart_game(self):
        for snd in list(self.active_sounds):
            sound.stop(snd)

        self.reset_game_state()
        self.set_difficulty(self.difficulty)
        if self.surface:
            self.load(self.surface)

    @property
    def ducks_missed(self): return self.ducks_missed_val
    @ducks_missed.setter
    def ducks_missed(self, val):
        self.ducks_missed_val = val
        if self.stage and self.stage.hud:
            if 'ducksMissed' not in self.stage.hud._items:
                self.stage.hud.create_texture_based_counter('ducksMissed', {
                    'texture': 'hud/score-live/0.png',
                    'location': Stage.missed_duck_status_box_location(),
                    'rowMax': 20,
                    'max': 20
                })
            self.stage.hud.ducksMissed = val

    @property
    def ducks_shot(self): return self.ducks_shot_val
    @ducks_shot.setter
    def ducks_shot(self, val):
        self.ducks_shot_val = val
        if self.stage and self.stage.hud:
            if 'ducksShot' not in self.stage.hud._items:
                self.stage.hud.create_texture_based_counter('ducksShot', {
                    'texture': 'hud/score-dead/0.png',
                    'location': Stage.dead_duck_status_box_location(),
                    'rowMax': 20,
                    'max': 20
                })
            self.stage.hud.ducksShot = val

    @property
    def bullets(self): return self.bullet_val
    @bullets.setter
    def bullets(self, val):
        self.bullet_val = val
        if self.stage and self.stage.hud:
            if 'bullets' not in self.stage.hud._items:
                self.stage.hud.create_texture_based_counter('bullets', {
                    'texture': 'hud/bullet/0.png',
                    'location': Stage.bullet_status_box_location(),
                    'rowMax': 20,
                    'max': 80
                })
            self.stage.hud.bullets = val

    @property
    def lives(self): return self.lives_val
    @lives.setter
    def lives(self, val):
        self.lives_val = max(0, val)
        if self.stage and self.stage.hud:
            if 'lives' not in self.stage.hud._items:
                self.stage.hud.create_texture_based_counter('lives', {
                    'texture': 'hud/hearts/full.png',
                    'emptyTexture': 'hud/hearts/empty.png',
                    'location': Stage.lives_box_location(),
                    'max': MAX_LIVES,
                    'iconScale': 0.12
                })
            self.stage.hud.lives = self.lives_val

    @property
    def score(self): return self.score_val
    @score.setter
    def score(self, val):
        self.score_val = val
        if self.stage and self.stage.hud:
            if 'score' not in self.stage.hud._items:
                self.stage.hud.create_text_box('score', {
                    'style': {'fontFamily': 'Arial', 'fontSize': '18px', 'fill': 'white'},
                    'location': Stage.score_box_location(),
                    'anchor': (1, 0)
                })
            self.stage.hud.score = val

    @property
    def wave(self): return self.wave_val
    @wave.setter
    def wave(self, val):
        self.wave_val = val
        if self.stage and self.stage.hud:
            if 'waveStatus' not in self.stage.hud._items:
                self.stage.hud.create_text_box('waveStatus', {
                    'style': {'fontFamily': 'Arial', 'fontSize': '14px', 'fill': 'white'},
                    'location': Stage.wave_status_box_location(),
                    'anchor': (1, 1)
                })
            if val is not None and val > 0:
                self.stage.hud.waveStatus = f"wave {val} of {self.level['waves']}"
            else:
                self.stage.hud.waveStatus = ""

    @property
    def game_status(self): return self.game_status_val
    @game_status.setter
    def game_status(self, val):
        self.game_status_val = val
        if self.stage and self.stage.hud:
            if 'gameStatus' not in self.stage.hud._items:
                self.stage.hud.create_text_box('gameStatus', {
                    'style': {'fontFamily': 'Arial', 'fontSize': '40px', 'fill': 'white'},
                    'location': Stage.game_status_box_location()
                })
            self.stage.hud.gameStatus = val

    def load(self, surface):
        self.surface = surface
        self.stage = Stage({'spritesheet': self.spritesheet})
        
        self.add_fullscreen_link()
        self.add_mute_link()
        self.add_pause_link()
        self.add_link_to_level_creator()
        self.lives = self.lives_val
        
        self.start_level()

    def add_fullscreen_link(self):
        self.stage.hud.create_text_box('fullscreenLink', {
            'style': BOTTOM_LINK_STYLE,
            'location': Stage.fullscreen_link_box_location(),
            'anchor': (1, 1)
        })
        self.stage.hud.fullscreenLink = 'unfullscreen (f)' if self.is_fullscreen else 'fullscreen (f)'

    def add_mute_link(self):
        self.stage.hud.create_text_box('muteLink', {
            'style': BOTTOM_LINK_STYLE,
            'location': Stage.mute_link_box_location(),
            'anchor': (1, 1)
        })
        self.stage.hud.muteLink = 'unmute (m)' if self.is_muted else 'mute (m)'

    def add_pause_link(self):
        self.stage.hud.create_text_box('pauseLink', {
            'style': BOTTOM_LINK_STYLE,
            'location': Stage.pause_link_box_location(),
            'anchor': (1, 1)
        })
        self.stage.hud.pauseLink = 'unpause (p)' if self.is_paused else 'pause (p)'

    def add_link_to_level_creator(self):
        self.stage.hud.create_text_box('levelCreatorLink', {
            'style': BOTTOM_LINK_STYLE,
            'location': Stage.level_creator_link_box_location(),
            'anchor': (1, 1)
        })
        self.stage.hud.levelCreatorLink = self.difficulty_link_text()

    def handle_keydown(self, key):
        if key == pygame.K_p:
            self.pause()
        elif key == pygame.K_m:
            self.mute()
        elif key == pygame.K_c:
            self.cycle_difficulty()
        elif key == pygame.K_f:
            self.fullscreen()

    def fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.stage.hud.fullscreenLink = 'unfullscreen (f)'
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.stage.hud.fullscreenLink = 'fullscreen (f)'
            pygame.display.set_mode((800, 600), pygame.RESIZABLE)

    def pause(self):
        self.is_paused = not self.is_paused
        self.stage.hud.pauseLink = 'unpause (p)' if self.is_paused else 'pause (p)'
        if self.is_paused:
            self.pause_start_time = time.time()
            self.stage.pause()
            for snd in self.active_sounds:
                sound.pause(snd)
        else:
            self.time_paused += time.time() - self.pause_start_time
            self.stage.resume()
            for snd in self.active_sounds:
                sound.resume(snd)

    def mute(self):
        self.is_muted = not self.is_muted
        self.stage.hud.muteLink = 'unmute (m)' if self.is_muted else 'mute (m)'
        sound.mute(self.is_muted)

    def start_level(self):
        self.state = 'PLAYING'
        self.is_game_over = False
        self.level = self.levels[self.level_index]
        self.max_score += self.level['waves'] * self.level['ducks'] * self.level['pointsPerDuck']
        self.ducks_shot = 0
        self.ducks_missed = 0
        self.wave = 0
        self.game_status = self.level['title']
        
        def on_pre_level_complete():
            self.game_status = ''
            self.start_wave()
            
        self.stage.pre_level_animation(on_pre_level_complete)

    def start_wave(self):
        self.state = 'PLAYING'
        self.quacking_sound_id = sound.play('quacking', loop=-1)
        if self.quacking_sound_id and self.quacking_sound_id not in self.active_sounds:
            self.active_sounds.append(self.quacking_sound_id)
            
        self.wave += 1
        self.wave_start_time = time.time()
        self.bullets = self.level['bullets']
        self.ducks_shot_this_wave = 0
        self.wave_ending = False
        
        self.stage.add_ducks(self.level['ducks'], self.level['speed'])

    def end_wave(self):
        self.wave_ending = True
        self.bullets = 0
        sound.stop(self.quacking_sound_id)
        if self.quacking_sound_id in self.active_sounds:
            self.active_sounds.remove(self.quacking_sound_id)
            
        if self.stage.ducks_alive():
            self.ducks_missed += self.level['ducks'] - self.ducks_shot_this_wave
            self.bg_color = PINK_SKY_COLOR
            self.lives -= 1
            self.stage.fly_away(self.go_to_next_wave)
        else:
            self.stage.clean_up_ducks()
            self.go_to_next_wave()

    def go_to_next_wave(self):
        if self.lives <= 0:
            self.game_over()
            return

        self.bg_color = BLUE_SKY_COLOR
        if self.level['waves'] == self.wave:
            self.end_level()
        else:
            self.start_wave()

    def should_wave_end(self):
        if self.wave == 0 or self.wave_ending or self.stage.dog_active():
            return False
        return self.is_wave_time_up() or (self.out_of_ammo() and self.stage.ducks_alive()) or not self.stage.ducks_active()

    def is_wave_time_up(self):
        if not self.level: return False
        return self.wave_elapsed_time() >= self.level['time']

    def wave_elapsed_time(self):
        return (time.time() - self.wave_start_time) - self.time_paused

    def out_of_ammo(self):
        return self.level is not None and self.bullets == 0

    def end_level(self):
        self.wave = 0
        self.go_to_next_level()

    def go_to_next_level(self):
        self.level_index += 1
        if not self.level_won():
            self.loss()
        elif self.level_index < len(self.levels):
            self.start_level()
        else:
            self.win()

    def level_won(self):
        return self.ducks_shot > SUCCESS_RATIO * self.level['ducks'] * self.level['waves']

    def win(self):
        self.state = 'WIN'
        snd_id = sound.play('champ')
        if snd_id: self.active_sounds.append(snd_id)
        self.game_status = 'You Win!'
        self.show_replay(self.get_score_message())

    def loss(self):
        self.state = 'LOSS'
        snd_id = sound.play('loserSound')
        if snd_id: self.active_sounds.append(snd_id)
        self.game_status = 'You Lose!'
        self.show_replay(self.get_score_message())

    def game_over(self):
        if self.is_game_over:
            return

        self.state = 'GAME_OVER'
        self.is_game_over = True
        snd_id = sound.play('loserSound')
        if snd_id: self.active_sounds.append(snd_id)
        self.game_status = 'Game Over'
        self.show_replay('Game Over.')

    def get_score_message(self):
        percentage = (self.score / self.max_score) * 100 if self.max_score > 0 else 0
        if percentage == 100: return 'Flawless victory.'
        if percentage < 100 and percentage > 95: return 'Close to perfection.'
        if percentage <= 95 and percentage > 85: return 'Truly impressive score.'
        if percentage <= 85 and percentage > 75: return 'Solid score.'
        if percentage <= 75 and percentage > 63: return 'Participation award.'
        return 'Yikes.'

    def show_replay(self, replay_text):
        self.stage.hud.create_text_box('replayButton', {
            'location': Stage.replay_button_location()
        })
        self.stage.hud.replayButton = replay_text + ' Play Again?'

    def handle_click(self, click_point):
        if self.stage.clicked_pause_link(click_point):
            self.pause()
            return
        if self.stage.clicked_mute_link(click_point):
            self.mute()
            return
        if self.stage.clicked_fullscreen_link(click_point):
            self.fullscreen()
            return
        if self.stage.clicked_level_creator_link(click_point):
            self.cycle_difficulty()
            return
            
        has_replay = hasattr(self.stage.hud, '_items') and 'replayButton' in self.stage.hud._items
            
        if not has_replay and not self.out_of_ammo() and not self.should_wave_end() and not self.is_paused:
            snd_id = sound.play('gunSound')
            if snd_id: self.active_sounds.append(snd_id)
            self.bullets -= 1
            ducks_shot = self.stage.shots_fired(click_point, self.level['radius'])
            self.update_score(ducks_shot)
            return

        if has_replay and self.stage.clicked_replay(click_point):
            self.restart_game()

    def update_score(self, ducks_shot):
        self.ducks_shot += ducks_shot
        self.ducks_shot_this_wave += ducks_shot
        self.score += ducks_shot * self.level['pointsPerDuck']

    def update(self, dt):
        if not self.is_paused and self.state == 'PLAYING':
            self.stage.update(dt)
            if self.should_wave_end():
                self.end_wave()

    def draw(self):
        if self.surface:
            self.surface.fill(self.bg_color)
            if self.stage:
                self.stage.draw(self.surface)
