import pygame
from libs.assets import Assets


def _clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

class TextBox:
    def __init__(self, text, style, location, anchor):
        self.text = text
        self.style = style
        self.location = location
        self.anchor = anchor
        font_name = style.get('fontFamily', 'Arial').lower()
        font_size = int(style.get('fontSize', '18px').replace('px', ''))
        self.font = pygame.font.SysFont(font_name, font_size)
        self.color = style.get('fill', (255, 255, 255))
        self.has_shadow = style.get('shadow', True)
        self.shadow_color = style.get('shadowColor', (20, 25, 35))
        self.is_button = style.get('isButton', False)
        
    def draw(self, surface, scale_x=1.0, scale_y=1.0):
        if not self.text: return
        
        # Render main text
        text_surface = self.font.render(str(self.text), True, self.color)
        rect = text_surface.get_rect()
        
        x = int((self.location[0] - rect.width * self.anchor[0]) * scale_x)
        y = int((self.location[1] - rect.height * self.anchor[1]) * scale_y)
        
        if self.is_button:
            # Draw a button capsule background (Dark Navy/Slate instead of Black)
            padding_x, padding_y = 14 * scale_x, 8 * scale_y
            btn_rect = pygame.Rect(x - padding_x, y - padding_y, rect.width + padding_x * 2, rect.height + padding_y * 2)
            pygame.draw.rect(surface, (25, 35, 50, 190), btn_rect, border_radius=int(12 * scale_x))
            pygame.draw.rect(surface, (200, 210, 230, 150), btn_rect, width=2, border_radius=int(12 * scale_x))

        if self.has_shadow:
            shadow_surface = self.font.render(str(self.text), True, self.shadow_color)
            surface.blit(shadow_surface, (x + 2, y + 2))
            
        surface.blit(text_surface, (x, y))

class TextureCounter:
    def __init__(self, texture_key, location, max_val, row_max, icon_scale=1.0):
        self.texture_key = texture_key
        self.location = location
        self.max_val = max_val
        self.row_max = row_max
        self.icon_scale = icon_scale
        self.value = 0
        self.texture = Assets.get_texture(texture_key)

    def _get_draw_texture(self):
        if not self.texture:
            return None
        if self.icon_scale == 1.0:
            return self.texture

        width = max(1, int(self.texture.get_width() * self.icon_scale))
        height = max(1, int(self.texture.get_height() * self.icon_scale))
        return pygame.transform.smoothscale(self.texture, (width, height))
        
    def draw(self, surface, scale_x=1.0, scale_y=1.0):
        draw_texture = self._get_draw_texture()
        if not draw_texture: return
        val = min(self.value, self.max_val) if self.max_val else self.value
        
        width = draw_texture.get_width()
        height = draw_texture.get_height()
        
        # Subtle semi-transparent panel for counters
        if val > 0:
            bg_width = (width * min(val, self.row_max if self.row_max else val)) + 12
            bg_height = height + 8
            bg_rect = pygame.Rect(int(self.location[0] * scale_x) - 6, int(self.location[1] * scale_y) - 4, bg_width, bg_height)
            pygame.draw.rect(surface, (15, 20, 30, 140), bg_rect, border_radius=6)
            pygame.draw.rect(surface, (255, 255, 255, 40), bg_rect, width=1, border_radius=6)

        for i in range(val):
            y_pos = 0
            x_pos_delta = i
            if self.row_max and self.row_max < val:
                y_pos = height * (i // self.row_max)
                x_pos_delta = i % self.row_max
            
            x = int((self.location[0] + width * x_pos_delta) * scale_x)
            y = int((self.location[1] + y_pos) * scale_y)
            
            surface.blit(draw_texture, (x, y))

class LivesCounter:
    def __init__(self, full_texture_key, empty_texture_key, location, max_val, icon_scale=1.0):
        self.full_texture = Assets.get_texture(full_texture_key)
        self.empty_texture = Assets.get_texture(empty_texture_key)
        self.location = location
        self.max_val = max_val
        self.icon_scale = icon_scale
        self._value = 0
        self._loss_animation_index = None
        self._loss_animation_start_ms = 0
        self._loss_animation_duration_ms = 240

    def _scale_texture(self, texture):
        if not texture:
            return None
        if self.icon_scale == 1.0:
            return texture

        width = max(1, int(texture.get_width() * self.icon_scale))
        height = max(1, int(texture.get_height() * self.icon_scale))
        return pygame.transform.smoothscale(texture, (width, height))

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        old_value = self._value
        self._value = new_value

        if new_value < old_value:
            self._loss_animation_index = max(0, old_value - 1)
            self._loss_animation_start_ms = pygame.time.get_ticks()

    def _draw_loss_animation(self, surface, full_texture, icon_x, icon_y):
        if self._loss_animation_index is None:
            return

        elapsed_ms = pygame.time.get_ticks() - self._loss_animation_start_ms
        if elapsed_ms >= self._loss_animation_duration_ms:
            self._loss_animation_index = None
            return

        progress = elapsed_ms / self._loss_animation_duration_ms
        pulse = 1.0 + (0.4 * progress)
        alpha = max(0, int(255 * (1.0 - progress)))

        anim_width = max(1, int(full_texture.get_width() * pulse))
        anim_height = max(1, int(full_texture.get_height() * pulse))
        anim_texture = pygame.transform.smoothscale(full_texture, (anim_width, anim_height))
        anim_texture.set_alpha(alpha)

        offset_x = int((anim_width - full_texture.get_width()) / 2)
        offset_y = int((anim_height - full_texture.get_height()) / 2)
        surface.blit(anim_texture, (icon_x - offset_x, icon_y - offset_y))

    def draw(self, surface, scale_x=1.0, scale_y=1.0):
        full_texture = self._scale_texture(self.full_texture)
        empty_texture = self._scale_texture(self.empty_texture)

        draw_texture = full_texture if full_texture else empty_texture
        if not draw_texture:
            return

        max_lives = max(0, self.max_val)
        current_lives = max(0, min(self.value, max_lives))
        icon_width = draw_texture.get_width()

        # Semi-transparent backing for lives bar
        bar_rect = pygame.Rect(int(self.location[0] * scale_x) - 6, int(self.location[1] * scale_y) - 4, 
                               int(icon_width * max_lives * scale_x) + 12, int(draw_texture.get_height() * scale_y) + 8)
                               
        bar_surf = pygame.Surface((bar_rect.width, bar_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bar_surf, (20, 30, 45, 140), bar_surf.get_rect(), border_radius=10)
        pygame.draw.rect(bar_surf, (255, 255, 255, 60), bar_surf.get_rect(), width=1, border_radius=10)
        surface.blit(bar_surf, bar_rect)

        for i in range(max_lives):
            x = int((self.location[0] + icon_width * i) * scale_x)
            y = int(self.location[1] * scale_y)

            if empty_texture:
                surface.blit(empty_texture, (x, y))

            if i < current_lives and full_texture:
                surface.blit(full_texture, (x, y))

            if full_texture and i == self._loss_animation_index:
                self._draw_loss_animation(surface, full_texture, x, y)


class WaveProgressPanel:
    def __init__(self):
        self.game = None
        self.wave_font = pygame.font.SysFont('arial', 20, bold=True)
        self.ducks_font = pygame.font.SysFont('arial', 16)
        self.message_font = pygame.font.SysFont('arial', 26, bold=True)

        self.panel_width = 320
        self.panel_height = 90
        self.panel_margin_top = 10
        self.corner_radius = 12

        self.border_color = (255, 215, 0) # Gold
        self.wave_color = (255, 255, 255)
        self.ducks_color = (240, 240, 240)
        self.bar_bg_color = (30, 40, 55)
        self.bar_fill_color = (50, 205, 50) # Lime Green
        self.percent_color = (255, 255, 0)
        self.message_color = (255, 255, 255)

        self.message_text = ''
        self.message_until_ms = 0
        self.message_duration_ms = 2500

        self._initialized = False
        self._last_wave = 0
        self._last_level_index = 0

    def bind_game(self, game):
        self.game = game
        self._initialized = False

    def _read_progress(self):
        if not self.game:
            return None

        level = getattr(self.game, 'level', None) or {}
        wave = max(0, int(getattr(self.game, 'wave', 0) or 0))
        total_waves = max(0, int(level.get('waves', 0) or 0))
        ducks_hit = max(0, int(getattr(self.game, 'ducks_shot_this_wave', 0) or 0))
        ducks_total = max(0, int(level.get('ducks', 0) or 0))
        level_index = int(getattr(self.game, 'level_index', 0) or 0)

        return {
            'wave': wave,
            'total_waves': total_waves,
            'ducks_hit': ducks_hit,
            'ducks_total': ducks_total,
            'level_index': level_index,
        }

    def _update_message(self, progress):
        now_ms = pygame.time.get_ticks()

        if not self._initialized:
            self._last_wave = progress['wave']
            self._last_level_index = progress['level_index']
            self._initialized = True
            return

        if progress['level_index'] > self._last_level_index:
            self.message_text = '¡NIVEL COMPLETADO!'
            self.message_until_ms = now_ms + self.message_duration_ms
        elif progress['wave'] > self._last_wave and self._last_wave > 0:
            self.message_text = '¡OLEADA COMPLETADA!'
            self.message_until_ms = now_ms + self.message_duration_ms

        self._last_wave = progress['wave']
        self._last_level_index = progress['level_index']

    def draw(self, surface, scale_x=1.0, scale_y=1.0):
        progress = self._read_progress()
        if not progress or progress['wave'] == 0:
            return

        self._update_message(progress)

        wave_text = f"OLEADA {progress['wave']} / {progress['total_waves']}"
        ducks_text = f"PATOS: {progress['ducks_hit']} / {progress['ducks_total']}"

        ratio = 0.0
        if progress['ducks_total'] > 0:
            ratio = _clamp(progress['ducks_hit'] / progress['ducks_total'], 0.0, 1.0)
        percent = int(round(ratio * 100))

        center_x = int(400 * scale_x)
        panel_y = int(self.panel_margin_top * scale_y)
        
        # Draw Glassy Minimalist Panel (Highly transparent navy-slate)
        panel_rect = pygame.Rect(center_x - int(160 * scale_x), panel_y, int(320 * scale_x), int(80 * scale_y))
        
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (20, 30, 45, 140), panel_surf.get_rect(), border_radius=12)
        pygame.draw.rect(panel_surf, (255, 255, 255, 60), panel_surf.get_rect(), width=1, border_radius=12)
        surface.blit(panel_surf, panel_rect)

        wave_surface = self.wave_font.render(wave_text, True, self.wave_color)
        ducks_surface = self.ducks_font.render(ducks_text, True, self.ducks_color)
        percent_surface = self.ducks_font.render(f"{percent}%", True, self.percent_color)

        wave_rect = wave_surface.get_rect(center=(center_x, panel_y + int(22 * scale_y)))
        ducks_rect = ducks_surface.get_rect(center=(center_x, panel_y + int(45 * scale_y)))
        surface.blit(wave_surface, wave_rect)
        surface.blit(ducks_surface, ducks_rect)

        bar_width = max(1, int(220 * scale_x))
        bar_height = max(1, int(12 * scale_y))
        bar_x = center_x - (bar_width // 2)
        bar_y = panel_y + int(60 * scale_y)

        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        fill_width = int((bar_width - 2) * ratio)
        fill_rect = pygame.Rect(bar_x + 1, bar_y + 1, max(0, fill_width), max(1, bar_height - 2))

        pygame.draw.rect(surface, self.bar_bg_color, bg_rect, border_radius=6)
        if fill_rect.width > 0:
            pygame.draw.rect(surface, self.bar_fill_color, fill_rect, border_radius=6)
        pygame.draw.rect(surface, (210, 210, 220, 100), bg_rect, width=1, border_radius=6)

        percent_rect = percent_surface.get_rect(midleft=(bar_x + bar_width + int(10 * scale_x), bar_y + (bar_height // 2)))
        surface.blit(percent_surface, percent_rect)

        now_ms = pygame.time.get_ticks()
        if self.message_text and now_ms <= self.message_until_ms:
            # Pulsing effect for message
            alpha = int(160 + 95 * abs(pygame.time.get_ticks() % 1000 - 500) / 500)
            message_surface = self.message_font.render(self.message_text, True, self.message_color)
            message_surface.set_alpha(alpha)
            message_rect = message_surface.get_rect(center=(center_x, panel_y + int(112 * scale_y)))
            
            # Shadow for message
            shadow_surface = self.message_font.render(self.message_text, True, (25, 30, 40))
            shadow_rect = shadow_surface.get_rect(center=(center_x + 2, panel_y + int(114 * scale_y)))
            surface.blit(shadow_surface, shadow_rect)
            surface.blit(message_surface, message_rect)

class Hud:
    def __init__(self):
        self._items = {}
        self._values = {}
        self._game = None
        self._wave_progress_panel = WaveProgressPanel()

    def bind_game(self, game):
        self._game = game
        self._wave_progress_panel.bind_game(game)

    def create_text_box(self, name, opts=None):
        if opts is None: opts = {}
        style = opts.get('style', {'fontFamily': 'Arial', 'fontSize': '18px', 'fill': 'white'})
        location = opts.get('location', (0, 0))
        anchor = opts.get('anchor', (0.5, 0.5))
        
        self._items[name] = TextBox("", style, location, anchor)
        self._values[name] = ""

    def create_texture_based_counter(self, name, opts=None):
        if opts is None: opts = {}
        texture = opts.get('texture', '')
        empty_texture = opts.get('emptyTexture', None)
        location = opts.get('location', (0, 0))
        max_val = opts.get('max', None)
        row_max = opts.get('rowMax', None)
        icon_scale = opts.get('iconScale', 1.0)
        
        if empty_texture:
            self._items[name] = LivesCounter(texture, empty_texture, location, max_val, icon_scale)
        else:
            self._items[name] = TextureCounter(texture, location, max_val, row_max, icon_scale)
        self._values[name] = 0

    def __getattr__(self, name):
        if name in self._values:
            return self._values[name]
        raise AttributeError(f"'Hud' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in ['_items', '_values', '_game', '_wave_progress_panel']:
            super().__setattr__(name, value)
        elif hasattr(self, '_items') and name in self._items:
            self._values[name] = value
            if isinstance(self._items[name], TextBox):
                self._items[name].text = str(value)
            elif isinstance(self._items[name], (TextureCounter, LivesCounter)):
                self._items[name].value = value
        else:
            super().__setattr__(name, value)

    def draw(self, surface, scale_x=1.0, scale_y=1.0):
        for item in self._items.values():
            item.draw(surface, scale_x, scale_y)
        game = getattr(self, '_game', None)
        if game is not None and getattr(game, 'state', None) == 'PLAYING':
            self._wave_progress_panel.draw(surface, scale_x, scale_y)
