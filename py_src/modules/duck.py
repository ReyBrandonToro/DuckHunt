import random
from libs.utils import point_distance, direction_of_travel
from modules.character import Character
from modules.sound import sound
from libs.random_generators.LinearCongruentialGenerator import LinearCongruentialGenerator


rng = LinearCongruentialGenerator()
DEATH_ANIMATION_SECONDS = 0.6
RANDOM_FLIGHT_DELTA = 300

class Duck(Character):
    def __init__(self, options):
        sprite_id = 'duck/' + options.get('colorProfile', 'black')
        states = [
            {'name': 'left', 'animationSpeed': 0.18},
            {'name': 'right', 'animationSpeed': 0.18},
            {'name': 'top-left', 'animationSpeed': 0.18},
            {'name': 'top-right', 'animationSpeed': 0.18},
            {'name': 'dead', 'animationSpeed': 0.18},
            {'name': 'shot', 'animationSpeed': 0.18}
        ]
        super().__init__(sprite_id, states)
        self.alive = True
        self.visible = True
        self.options = options
        self.anchor = (0.5, 0.5)
        self.speed_val = 1
        self.flight_animation_ms = 1000

    @property
    def speed(self):
        return self.speed_val

    @speed.setter
    def speed(self, val):
        flight_animation_ms = 1000
        if val == 0: flight_animation_ms = 3000
        elif val == 1: flight_animation_ms = 2800
        elif val == 2: flight_animation_ms = 2500
        elif val == 3: flight_animation_ms = 2000
        elif val == 4: flight_animation_ms = 1800
        elif val == 5: flight_animation_ms = 1500
        elif val == 6: flight_animation_ms = 1300
        elif val == 7: flight_animation_ms = 1200
        elif val == 8: flight_animation_ms = 800
        elif val == 9: flight_animation_ms = 600
        elif val == 10: flight_animation_ms = 500
        self.speed_val = val
        self.flight_animation_ms = flight_animation_ms

    def random_flight(self, opts=None):
        if opts is None: opts = {}
        min_x = opts.get('minX', 0)
        max_x = opts.get('maxX', self.options.get('maxX', 800))
        min_y = opts.get('minY', 0)
        max_y = opts.get('maxY', self.options.get('maxY', 600))
        random_flight_delta = opts.get('randomFlightDelta', self.options.get('randomFlightDelta', RANDOM_FLIGHT_DELTA))
        speed = opts.get('speed', 1)

        while True:
            #dest_x = random.randint(min_x, max_x)
            dest_x = rng.randint(min_x, max_x)
            #dest_y = random.randint(min_y, max_y)
            dest_y = rng.randint(min_y, max_y)
            dist = point_distance((self.x, self.y), (dest_x, dest_y))
            if dist >= random_flight_delta:
                break

        def on_complete():
            self.random_flight(opts)
            
        self.fly_to({
            'point': (dest_x, dest_y),
            'speed': speed,
            'onComplete': on_complete
        })

    def fly_to(self, opts):
        point = opts.get('point', (self.x, self.y))
        speed = opts.get('speed', self.speed)
        on_start = opts.get('onStart', lambda: None)
        on_complete = opts.get('onComplete', lambda: None)

        self.speed = speed

        direction = direction_of_travel((self.x, self.y), point)
        tween_seconds = (self.flight_animation_ms + random.randint(0, 300)) / 1000.0

        def start_func():
            if not self.alive:
                self.stop_and_clear_timeline()
            self.play()
            self.state = direction.replace('bottom', 'top')
            on_start()

        self.timeline.to(self, tween_seconds, x=point[0], y=point[1], ease='none', onStart=start_func, onComplete=on_complete)
        return self

    def shot(self):
        if not self.alive:
            return
        self.alive = False

        self.stop_and_clear_timeline()
        
        def initial_shot():
            self.state = 'shot'
            sound.play('quak')
        self.timeline.call(initial_shot)

        def dead_start():
            self.state = 'dead'
            
        def dead_complete():
            sound.play('thud')
            self.visible = False

        self.timeline.to(self, DEATH_ANIMATION_SECONDS, y=self.options.get('maxY', 600), ease='none', delay=0.3, onStart=dead_start, onComplete=dead_complete)

    def is_active(self):
        return self.visible or super().is_active()
