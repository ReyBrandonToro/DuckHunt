import time

class CustomRandom:
    def __init__(self, method='lcg', seed=None):
        # Si no hay semilla, usamos el reloj del sistema
        self.seed = seed if seed is not None else int(time.time())
        self.method = method
        
        # Parámetros LCG (estándar de glibc)
        self.a = 1103515245
        self.c = 12345
        self.m = 2**31

    def _lcg(self):
        self.seed = (self.a * self.seed + self.c) % self.m
        return self.seed / self.m

    def _middle_square(self):
        # Aseguramos que la semilla tenga 4 dígitos para estabilidad
        s_seed = str(self.seed**2).zfill(8)
        # Tomamos los 4 dígitos centrales
        mid = int(s_seed[2:6])
        self.seed = mid
        return mid / 10000

    def randint(self, a, b):
        """Devuelve un entero aleatorio entre a y b (inclusive)"""
        if self.method == 'lcg':
            r = self._lcg()
        else:
            r = self._middle_square()
            
        # Transformación de rango lineal: a + r * (b - a + 1)
        return int(a + r * (b - a + 1))
