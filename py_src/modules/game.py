import pygame
import time
import json
import os
from modules.stage import Stage
from modules.sound import sound

BLUE_SKY_COLOR = (100, 176, 255)
PINK_SKY_COLOR = (251, 180, 212)
SUCCESS_RATIO = 0.6
BOTTOM_LINK_STYLE = {'fontFamily': 'Arial', 'fontSize': '15px', 'fill': 'white', 'isButton': True}
DIFFICULTY_ORDER = ('easy', 'normal', 'hard')
MAX_LIVES = 3
DEFAULT_CREDITS = 5
CREDITS_RECHARGE_AMOUNT = 5
MAX_HIGH_SCORES = 10
DEFAULT_PLAYER_NAME = 'Player'

STATE_MENU = 'MENU'
STATE_PLAYING = 'PLAYING'
STATE_GAME_OVER = 'GAME_OVER'
STATE_RANKING = 'RANKING'
STATE_READY = 'READY'
STATE_WIN = 'WIN'
STATE_LOSS = 'LOSS'

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
        self.state = STATE_MENU
        self.is_game_over = False
        self.player_name = DEFAULT_PLAYER_NAME
        self._player_name_input = ''
        self.high_scores = []
        self._menu_text_font = None
        self._menu_title_font = None
        self._panel_surface = None

        self.wave_ending = False
        self.quacking_sound_id = None

        self.high_scores_path = self._data_file_path('highscores.json')

        with open(self._data_file_path('levels.json'), 'r') as f:
            self.levels_data = json.load(f)
        self.set_difficulty(self.difficulty)
        self.high_scores = self.load_high_scores()
        
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
        self.credits_val = DEFAULT_CREDITS
        self.demo_mode_val = False

    @property
    def credits(self):
        return self.credits_val

    @credits.setter
    def credits(self, val):
        self.credits_val = max(0, int(val or 0))
        self._refresh_credits_display()

    @property
    def demo_mode(self):
        return self.demo_mode_val

    @demo_mode.setter
    def demo_mode(self, enabled):
        self.demo_mode_val = bool(enabled)
        self._refresh_credits_display()

    def _data_file_path(self, filename):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_dir, 'data', filename)

    def _sanitize_player_name(self, name):
        clean_name = (name or '').strip()
        return clean_name if clean_name else DEFAULT_PLAYER_NAME

    def _initialize_ui_fonts(self):
        if self._menu_title_font is None:
            self._menu_title_font = pygame.font.SysFont('arial', 40, bold=True)
        if self._menu_text_font is None:
            self._menu_text_font = pygame.font.SysFont('arial', 24)

    def _make_panel_surface(self, width, height):
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((20, 30, 45, 170))
        return panel

    def _prepare_menu(self):
        self.state = STATE_MENU
        self.is_paused = False
        self.time_paused = 0
        self._player_name_input = self.player_name if self.player_name != DEFAULT_PLAYER_NAME else ''
        self._clear_game_over_prompt()
        self._refresh_credits_display()
        sound.play_music("It's Showtime!.mp3", loop=-1)

    def _start_gameplay_from_menu(self):
        self.player_name = self._sanitize_player_name(self._player_name_input)
        self._player_name_input = self.player_name
        self.reset_game_state(preserve_stage=True)
        self.add_fullscreen_link()
        self.add_mute_link()
        self.add_pause_link()
        self.add_link_to_level_creator()
        self.lives = MAX_LIVES
        self._clear_game_over_prompt()
        sound.play_music("DeathByGlamour.MP3", loop=-1)
        self.start_level()

    def _credits_text(self):
        return 'Credits: \u221e' if self.demo_mode else f'Credits: {self.credits}'

    def _refresh_credits_display(self):
        if not self.stage or not self.stage.hud:
            return

        if 'credits' not in self.stage.hud._items:
            self.stage.hud.create_text_box('credits', {
                'style': {'fontFamily': 'Arial', 'fontSize': '18px', 'fill': 'white'},
                'location': Stage.credits_box_location(),
                'anchor': (0, 0)
            })
        self.stage.hud.credits = self._credits_text()

    def _set_game_over_prompt(self, text):
        if not self.stage or not self.stage.hud:
            return

        if 'continuePrompt' not in self.stage.hud._items:
            self.stage.hud.create_text_box('continuePrompt', {
                'style': {'fontFamily': 'Arial', 'fontSize': '22px', 'fill': 'white'},
                'location': Stage.game_over_prompt_location(),
                'anchor': (0.5, 0.5)
            })
        self.stage.hud.continuePrompt = text

    def _clear_game_over_prompt(self):
        if not self.stage or not self.stage.hud:
            return
        if 'continuePrompt' in self.stage.hud._items:
            self.stage.hud.continuePrompt = ''

    def add_credits(self, amount=CREDITS_RECHARGE_AMOUNT):
        self.credits = self.credits + max(0, int(amount or 0))

    def toggle_demo_mode(self):
        self.demo_mode = not self.demo_mode

    def can_continue_after_game_over(self):
        return self.demo_mode or self.credits > 0

    def _consume_continue_credit(self):
        if self.demo_mode:
            return True
        if self.credits <= 0:
            return False
        self.credits -= 1
        return True

    def continue_after_game_over(self):
        if not self._consume_continue_credit():
            self.finish_run_and_return_to_menu()
            return

        self.is_game_over = False
        self.lives = MAX_LIVES
        self.wave = 0
        self.wave_ending = False
        self.bg_color = BLUE_SKY_COLOR
        self._clear_game_over_prompt()
        if self.stage:
            self.stage.clean_up_ducks()
        self.start_level()

    def finish_run_and_return_to_menu(self):
        self.update_high_scores(self.player_name, self.score)
        self._prepare_menu()

    def _high_score_lines(self):
        if not self.high_scores:
            return ['No scores yet.']

        lines = []
        for entry in self.high_scores[:MAX_HIGH_SCORES]:
            name = self._sanitize_player_name(entry.get('name', DEFAULT_PLAYER_NAME))
            score = int(entry.get('score', 0) or 0)
            lines.append(f"{name} - {score}")
        return lines

    def _is_valid_score_entry(self, entry):
        if not isinstance(entry, dict):
            return False
        if 'name' not in entry or 'score' not in entry:
            return False
        try:
            int(entry.get('score', 0))
        except (TypeError, ValueError):
            return False
        return True

    def load_high_scores(self):
        os.makedirs(os.path.dirname(self.high_scores_path), exist_ok=True)

        if not os.path.exists(self.high_scores_path):
            with open(self.high_scores_path, 'w', encoding='utf-8') as file:
                json.dump([], file, ensure_ascii=True, indent=2)
            return []

        try:
            with open(self.high_scores_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            data = []

        if not isinstance(data, list):
            data = []

        cleaned = []
        for entry in data:
            if not self._is_valid_score_entry(entry):
                continue
            cleaned.append({
                'name': self._sanitize_player_name(entry.get('name', DEFAULT_PLAYER_NAME)),
                'score': int(entry.get('score', 0) or 0)
            })

        cleaned.sort(key=lambda item: item['score'], reverse=True)
        cleaned = cleaned[:MAX_HIGH_SCORES]
        return cleaned

    def save_high_scores(self):
        os.makedirs(os.path.dirname(self.high_scores_path), exist_ok=True)
        try:
            with open(self.high_scores_path, 'w', encoding='utf-8') as file:
                json.dump(self.high_scores[:MAX_HIGH_SCORES], file, ensure_ascii=True, indent=2)
        except OSError:
            # Ignore persistence errors at runtime to avoid breaking gameplay.
            return

    def update_high_scores(self, player_name, score):
        safe_name = self._sanitize_player_name(player_name)
        safe_score = max(0, int(score or 0))

        existing = next((entry for entry in self.high_scores if entry['name'] == safe_name), None)
        if existing:
            existing['score'] = max(existing['score'], safe_score)
        else:
            self.high_scores.append({'name': safe_name, 'score': safe_score})

        self.high_scores.sort(key=lambda item: item['score'], reverse=True)
        self.high_scores = self.high_scores[:MAX_HIGH_SCORES]
        self.save_high_scores()

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

    def reset_game_state(self, preserve_stage=False):
        self.level_index = 0
        self.max_score = 0
        self.time_paused = 0
        self.is_paused = False
        self.active_sounds = []
        self.state = STATE_READY
        self.is_game_over = False
        self.wave_ending = False
        self.quacking_sound_id = None
        self.level = None
        if not preserve_stage:
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
        self.stage.hud.bind_game(self)
        
        self.add_fullscreen_link()
        self.add_mute_link()
        self.add_pause_link()
        self.add_link_to_level_creator()
        self.lives = self.lives_val

        self._initialize_ui_fonts()
        self._panel_surface = self._make_panel_surface(700, 440)
        self._refresh_credits_display()
        self._prepare_menu()

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

    def handle_keydown(self, key_or_event):
        event = key_or_event if hasattr(key_or_event, 'key') else None
        key = event.key if event else key_or_event

        if self.state == STATE_MENU:
            self.handle_menu_keydown(event, key)
            return

        if self.state == STATE_GAME_OVER:
            self.handle_game_over_keydown(key)
            return

        if self.state == STATE_RANKING:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                self._prepare_menu()
            return

        if key == pygame.K_p:
            self.pause()
        elif key == pygame.K_m:
            self.mute()
        elif key == pygame.K_c:
            self.cycle_difficulty()
        elif key == pygame.K_f:
            self.fullscreen()

    def handle_menu_keydown(self, event, key):
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._start_gameplay_from_menu()
            return

        if key == pygame.K_BACKSPACE:
            self._player_name_input = self._player_name_input[:-1]
            return

        if key == pygame.K_c:
            self.set_difficulty(DIFFICULTY_ORDER[(DIFFICULTY_ORDER.index(self.difficulty) + 1) % len(DIFFICULTY_ORDER)])
            return

        if key == pygame.K_F2:
            self.add_credits()
            return

        if key == pygame.K_F3:
            self.toggle_demo_mode()
            return

        # Capturar entrada de texto
        if event and hasattr(event, 'unicode') and event.unicode:
            # Permitir caracteres imprimibles (ASCII 32 en adelante)
            if ord(event.unicode) >= 32 and len(self._player_name_input) < 12:
                self._player_name_input += event.unicode

    def handle_game_over_keydown(self, key):
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.can_continue_after_game_over():
                self.continue_after_game_over()
            else:
                self.finish_run_and_return_to_menu()
            return

        if key == pygame.K_ESCAPE:
            self.finish_run_and_return_to_menu()

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
        self.state = STATE_PLAYING
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
        self.state = STATE_PLAYING
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
            self.game_over()
        elif self.level_index < len(self.levels):
            self.start_level()
        else:
            self.win()

    def level_won(self):
        return self.ducks_shot > SUCCESS_RATIO * self.level['ducks'] * self.level['waves']

    def win(self):
        self.state = STATE_WIN
        #snd_id = sound.play('champ')
        #if snd_id: self.active_sounds.append(snd_id)
        self.game_status = 'You Win!'
        self.show_replay(self.get_score_message())

    def loss(self):
        self.state = STATE_LOSS
        snd_id = sound.play('loserSound')
        if snd_id: self.active_sounds.append(snd_id)
        self.game_status = 'You Lose!'
        self.show_replay(self.get_score_message())

    def game_over(self):
        if self.is_game_over:
            return

        self.state = STATE_GAME_OVER
        self.is_game_over = True
        snd_id = sound.play('loserSound')
        if snd_id: self.active_sounds.append(snd_id)
        self.game_status = 'Game Over'
        if self.can_continue_after_game_over():
            self._set_game_over_prompt('Continue? (1 credit) ENTER=Yes ESC=Menu')
        else:
            self._set_game_over_prompt('No credits left. Returning to menu...')
            self.finish_run_and_return_to_menu()

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
        if self.state == STATE_MENU:
            # Desactivamos el inicio por clic para permitir escribir el nombre sin accidentes
            return

        if self.state == STATE_GAME_OVER:
            if self.can_continue_after_game_over():
                self.continue_after_game_over()
            else:
                self.finish_run_and_return_to_menu()
            return

        if self.state == STATE_RANKING:
            self._prepare_menu()
            return

        if self.state != STATE_PLAYING and self.state != STATE_WIN and self.state != STATE_LOSS and self.state != STATE_GAME_OVER:
            return

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
        if not self.is_paused and self.state == STATE_PLAYING:
            self.stage.update(dt)
            if self.should_wave_end():
                self.end_wave()

    def _draw_centered_text(self, surface, text, font, color, center):
        text_surface = font.render(text, True, color)
        rect = text_surface.get_rect(center=center)
        surface.blit(text_surface, rect)

    def draw_menu(self):
        if not self.surface:
            return

        width, height = self.surface.get_size()
        
        # 1. Glassy Panel Background
        panel_w, panel_h = max(1, int(width * 0.88)), max(1, int(height * 0.82))
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 25, 45, 215), (0, 0, panel_w, panel_h), border_radius=20)
        pygame.draw.rect(panel, (255, 255, 255, 60), (0, 0, panel_w, panel_h), width=2, border_radius=20)
        panel_rect = panel.get_rect(center=(width // 2, height // 2))
        self.surface.blit(panel, panel_rect)

        # 2. Title
        title_y = panel_rect.top + 60
        title_font = pygame.font.SysFont('arial', 60, bold=True)
        self._draw_centered_text(self.surface, 'DUCK HUNT', title_font, (15, 15, 25), (width // 2 + 4, title_y + 4))
        self._draw_centered_text(self.surface, 'DUCK HUNT', title_font, (255, 215, 0), (width // 2, title_y))

        # 3. Subtitles
        info_y = title_y + 75
        self._draw_centered_text(self.surface, f'DIFFICULTY: {self.difficulty.upper()} (C)', self._menu_text_font, (235, 235, 235), (width // 2, info_y))
        self._draw_centered_text(self.surface, self._credits_text(), self._menu_text_font, (255, 255, 255), (width // 2, info_y + 35))
        
        # 4. Interactive Name Input
        display_name = self._player_name_input if self._player_name_input else DEFAULT_PLAYER_NAME
        input_y = info_y + 90
        cursor = '_' if (pygame.time.get_ticks() // 500) % 2 == 0 else ' '
        
        # Input Box
        pygame.draw.rect(self.surface, (240, 240, 245, 200), (width // 2 - 200, input_y - 25, 400, 50), border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255, 255), (width // 2 - 200, input_y - 25, 400, 50), width=2, border_radius=8)
        self._draw_centered_text(self.surface, f'PLAYER: {display_name}{cursor}', self._menu_text_font, (20, 25, 35), (width // 2, input_y))
        self._draw_centered_text(self.surface, 'PRESS ENTER TO START', pygame.font.SysFont('arial', 16, bold=True), (220, 220, 220), (width // 2, input_y + 42))

        # 5. Ranking Section
        ranking_y = input_y + 85
        self._draw_centered_text(self.surface, 'TOP 10 RANKING', pygame.font.SysFont('arial', 22, bold=True), (255, 232, 120), (width // 2, ranking_y))
        
        ranking_lines = self._high_score_lines()
        line_y = ranking_y + 35
        for i, line in enumerate(ranking_lines[:10]):
            color = (250, 250, 250) if i % 2 == 0 else (210, 210, 210)
            self._draw_centered_text(self.surface, f"{i+1}. {line}", pygame.font.SysFont('arial', 18), color, (width // 2, line_y))
            line_y += 24

    def draw_game_over(self):
        if not self.surface:
            return

        width, height = self.surface.get_size()
        panel_w = max(1, int(width * 0.82))
        panel_h = max(1, int(height * 0.72))
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        # Deep Maroon/Burgundy for Game Over
        pygame.draw.rect(panel, (55, 20, 20, 225), (0, 0, panel_w, panel_h), border_radius=20)
        pygame.draw.rect(panel, (255, 120, 120, 90), (0, 0, panel_w, panel_h), width=2, border_radius=20)
        
        panel_rect = panel.get_rect(center=(width // 2, height // 2))
        self.surface.blit(panel, panel_rect)

        title_y = panel_rect.top + 60
        self._draw_centered_text(self.surface, 'GAME OVER', pygame.font.SysFont('arial', 54, bold=True), (255, 90, 90), (width // 2, title_y))
        self._draw_centered_text(self.surface, f'FINAL SCORE: {self.score}', self._menu_text_font, (255, 255, 255), (width // 2, title_y + 65))
        self._draw_centered_text(self.surface, self._credits_text(), self._menu_text_font, (255, 255, 255), (width // 2, title_y + 100))

        prompt_y = title_y + 160
        if self.can_continue_after_game_over():
            self._draw_centered_text(self.surface, 'CONTINUE?', pygame.font.SysFont('arial', 28, bold=True), (255, 215, 0), (width // 2, prompt_y))
            self._draw_centered_text(self.surface, 'Uses 1 credit', pygame.font.SysFont('arial', 18), (210, 210, 210), (width // 2, prompt_y + 30))
            
            # Flashing interactive prompt
            hint_alpha = int(170 + 85 * abs(pygame.time.get_ticks() % 800 - 400) / 400)
            hint_font = pygame.font.SysFont('arial', 20, bold=True)
            hint_surface = hint_font.render('PRESS ENTER TO CONTINUE', True, (255, 255, 255))
            hint_surface.set_alpha(hint_alpha)
            self.surface.blit(hint_surface, hint_surface.get_rect(center=(width // 2, prompt_y + 75)))
            
            self._draw_centered_text(self.surface, 'PRESS ESC FOR MENU', pygame.font.SysFont('arial', 16), (170, 170, 170), (width // 2, prompt_y + 105))
        else:
            self._draw_centered_text(self.surface, 'OUT OF CREDITS', self._menu_text_font, (220, 60, 60), (width // 2, prompt_y + 20))
            self._draw_centered_text(self.surface, 'PRESS ENTER TO RETURN TO MENU', pygame.font.SysFont('arial', 18), (210, 210, 210), (width // 2, prompt_y + 70))

    def draw_ranking(self):
        if not self.surface:
            return

        width, height = self.surface.get_size()
        panel_w = max(1, int(width * 0.84))
        panel_h = max(1, int(height * 0.74))
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        # Deep Navy for Hall of Fame
        pygame.draw.rect(panel, (20, 30, 55, 220), (0, 0, panel_w, panel_h), border_radius=20)
        pygame.draw.rect(panel, (255, 255, 255, 60), (0, 0, panel_w, panel_h), width=2, border_radius=20)
        
        panel_rect = panel.get_rect(center=(width // 2, height // 2))
        self.surface.blit(panel, panel_rect)

        title_y = panel_rect.top + 50
        self._draw_centered_text(self.surface, 'HALL OF FAME', pygame.font.SysFont('arial', 42, bold=True), (255, 215, 0), (width // 2, title_y))
        self._draw_centered_text(self.surface, f'YOUR SCORE: {self.score}', self._menu_text_font, (255, 255, 255), (width // 2, title_y + 55))
        
        divider_y = title_y + 90
        pygame.draw.line(self.surface, (255, 255, 255, 90), (width // 2 - 220, divider_y), (width // 2 + 220, divider_y), width=2)

        line_y = divider_y + 35
        for i, line in enumerate(self._high_score_lines()[:10]):
            color = (250, 250, 250) if i % 2 == 0 else (190, 190, 190)
            self._draw_centered_text(self.surface, f"{i+1}. {line}", pygame.font.SysFont('arial', 20), color, (width // 2, line_y))
            line_y += 30

        hint_color = (210, 210, 210) if (pygame.time.get_ticks() // 600) % 2 == 0 else (130, 130, 130)
        self._draw_centered_text(self.surface, 'PRESS ENTER OR CLICK TO RETURN', pygame.font.SysFont('arial', 16, bold=True), hint_color, (width // 2, panel_rect.bottom - 45))

    def draw(self):
        if self.surface:
            self.surface.fill(self.bg_color)
            if self.stage:
                self.stage.draw(self.surface)
            if self.state == STATE_MENU:
                self.draw_menu()
            elif self.state == STATE_GAME_OVER:
                self.draw_game_over()
            elif self.state == STATE_RANKING:
                self.draw_ranking()
