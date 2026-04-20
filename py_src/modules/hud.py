import pygame
from libs.assets import Assets

class TextBox:
    def __init__(self, text, style, location, anchor):
        self.text = text
        self.style = style
        self.location = location
        self.anchor = anchor
        font_name = style.get('fontFamily', 'Arial').lower()
        font_size = int(style.get('fontSize', '18px').replace('px', ''))
        self.font = pygame.font.SysFont(font_name, font_size)
        self.color = (255, 255, 255)
        
    def draw(self, surface, scale_x=1.0, scale_y=1.0):
        if not self.text: return
        text_surface = self.font.render(str(self.text), True, self.color)
        rect = text_surface.get_rect()
        
        x = int((self.location[0] - rect.width * self.anchor[0]) * scale_x)
        y = int((self.location[1] - rect.height * self.anchor[1]) * scale_y)
        
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
        pulse = 1.0 + (0.22 * progress)
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

        for i in range(max_lives):
            x = int((self.location[0] + icon_width * i) * scale_x)
            y = int(self.location[1] * scale_y)

            if empty_texture:
                surface.blit(empty_texture, (x, y))

            if i < current_lives and full_texture:
                surface.blit(full_texture, (x, y))

            if full_texture and i == self._loss_animation_index:
                self._draw_loss_animation(surface, full_texture, x, y)

class Hud:
    def __init__(self):
        self._items = {}
        self._values = {}

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
        if name in ['_items', '_values']:
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
