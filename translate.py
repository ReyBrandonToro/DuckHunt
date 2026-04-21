import os

filepath = r"C:\Users\jsanc\OneDrive\Documentos\U\SEMESTRE-2026-1\MODELACION\DuckHunt\py_src\modules\game.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    "DEFAULT_PLAYER_NAME = 'Player'": "DEFAULT_PLAYER_NAME = 'Jugador'",
    "'Credits: \\u221e' if self.demo_mode else f'Credits: {self.credits}'": "'Créditos: \\u221e' if self.demo_mode else f'Créditos: {self.credits}'",
    "['No scores yet.']": "['Sin puntuaciones aún.']",
    'f"difficulty: {self.difficulty} (c)"': 'f"dificultad: {self.difficulty} (c)"',
    'f"wave {val} of {self.level[\'waves\']}"': 'f"oleada {val} de {self.level[\'waves\']}"',
    "self.game_status = 'You Win!'": "self.game_status = '¡Ganaste!'",
    "self.game_status = 'You Lose!'": "self.game_status = '¡Perdiste!'",
    "self.game_status = 'Game Over'": "self.game_status = 'Fin del Juego'",
    "self._set_game_over_prompt('Continue? (1 credit) ENTER=Yes ESC=Menu')": "self._set_game_over_prompt('¿Continuar? (1 crédito) ENTER=Sí ESC=Menú')",
    "self._set_game_over_prompt('No credits left. Returning to menu...')": "self._set_game_over_prompt('Sin créditos. Volviendo al menú...')",
    "return 'Flawless victory.'": "return 'Victoria perfecta.'",
    "return 'Close to perfection.'": "return 'Casi perfecto.'",
    "return 'Truly impressive score.'": "return 'Puntuación impresionante.'",
    "return 'Solid score.'": "return 'Puntuación sólida.'",
    "return 'Participation award.'": "return 'Premio de participación.'",
    "return 'Yikes.'": "return 'Uy.'",
    "replay_text + ' Play Again?'": "replay_text + ' ¿Jugar de nuevo?'",
    "'unfullscreen (f)' if self.is_fullscreen else 'fullscreen (f)'": "'pantalla chica (f)' if self.is_fullscreen else 'pantalla completa (f)'",
    "'unmute (m)' if self.is_muted else 'mute (m)'": "'activar sonido (m)' if self.is_muted else 'silenciar (m)'",
    "'unpause (p)' if self.is_paused else 'pause (p)'": "'reanudar (p)' if self.is_paused else 'pausar (p)'",
    "self.stage.hud.fullscreenLink = 'unfullscreen (f)'": "self.stage.hud.fullscreenLink = 'pantalla chica (f)'",
    "self.stage.hud.fullscreenLink = 'fullscreen (f)'": "self.stage.hud.fullscreenLink = 'pantalla completa (f)'",
    "self.stage.hud.pauseLink = 'unpause (p)' if self.is_paused else 'pause (p)'": "self.stage.hud.pauseLink = 'reanudar (p)' if self.is_paused else 'pausar (p)'",
    "self.stage.hud.muteLink = 'unmute (m)' if self.is_muted else 'mute (m)'": "self.stage.hud.muteLink = 'activar sonido (m)' if self.is_muted else 'silenciar (m)'",
    "f'DIFFICULTY: {self.difficulty.upper()} (C)'": "f'DIFICULTAD: {self.difficulty.upper()} (C)'",
    "f'PLAYER: {display_name}{cursor}'": "f'JUGADOR: {display_name}{cursor}'",
    "'PRESS ENTER TO START'": "'PRESIONA ENTER PARA INICIAR'",
    "'TOP 10 RANKING'": "'TOP 10 MEJORES'",
    "'GAME OVER'": "'FIN DEL JUEGO'",
    "f'FINAL SCORE: {self.score}'": "f'PUNTUACIÓN FINAL: {self.score}'",
    "'CONTINUE?'": "'¿CONTINUAR?'",
    "'Uses 1 credit'": "'Usa 1 crédito'",
    "'PRESS ENTER TO CONTINUE'": "'PRESIONA ENTER PARA CONTINUAR'",
    "'PRESS ESC FOR MENU'": "'PRESIONA ESC PARA EL MENÚ'",
    "'OUT OF CREDITS'": "'SIN CRÉDITOS'",
    "'PRESS ENTER TO RETURN TO MENU'": "'PRESIONA ENTER PARA VOLVER AL MENÚ'",
    "'HALL OF FAME'": "'SALÓN DE LA FAMA'",
    "f'YOUR SCORE: {self.score}'": "f'TU PUNTUACIÓN: {self.score}'",
    "'PRESS ENTER OR CLICK TO RETURN'": "'PRESIONA ENTER O HAZ CLIC PARA VOLVER'"
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Translations applied!")
