import pygame
import os

class SoundManager:
    def __init__(self):
        self._sounds = {}
        self.is_muted = False
        self.active_sounds = {}
        self._sound_id_counter = 0
        self.audio_dir = ""

    def init(self, audio_dir):
        self.audio_dir = audio_dir
        # Load individual audio files if available.
        # Howler in JS used audio sprite, but in Python it's easier if we use the loose MP3s.
        # I'll check src/assets/sounds/
        sounds = ['barkDucks', 'champ', 'gunSound', 'laugh', 'loserSound', 'ohYeah', 'quacking', 'quak', 'sniff', 'thud', 'Cuack', 'DuckDeath', 'ExperienceLevel']
        for s in sounds:
            path = os.path.join(audio_dir, f"{s}.mp3")
            path_upper = os.path.join(audio_dir, f"{s}.MP3")
            if os.path.exists(path):
                self._sounds[s] = pygame.mixer.Sound(path)
            elif os.path.exists(path_upper):
                self._sounds[s] = pygame.mixer.Sound(path_upper)

    def play_music(self, file_name, loop=-1):
        if not self.audio_dir:
            return
        path = os.path.join(self.audio_dir, file_name)
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops=loop)
            if self.is_muted:
                pygame.mixer.music.set_volume(0)
            else:
                pygame.mixer.music.set_volume(1)

    def stop_music(self):
        pygame.mixer.music.stop()

    def play(self, sound_name, loop=0):
        if sound_name not in self._sounds:
            return None
        
        if self.is_muted:
            return None

        sound = self._sounds[sound_name]
        channel = sound.play(loops=loop)
        
        self._sound_id_counter += 1
        self.active_sounds[self._sound_id_counter] = channel
        return self._sound_id_counter

    def stop(self, sound_id):
        if sound_id in self.active_sounds and self.active_sounds[sound_id] is not None:
            self.active_sounds[sound_id].stop()
            del self.active_sounds[sound_id]

    def pause(self, sound_id):
        if sound_id in self.active_sounds and self.active_sounds[sound_id] is not None:
            self.active_sounds[sound_id].pause()

    def resume(self, sound_id):
        if sound_id in self.active_sounds and self.active_sounds[sound_id] is not None:
            self.active_sounds[sound_id].unpause()

    def mute(self, is_muted):
        self.is_muted = is_muted
        if self.is_muted:
            for ch in self.active_sounds.values():
                if ch:
                    ch.set_volume(0)
            pygame.mixer.music.set_volume(0)
        else:
            for ch in self.active_sounds.values():
                if ch:
                    ch.set_volume(1)
            pygame.mixer.music.set_volume(1)

sound = SoundManager()
