# libs/lcg.py
import time

class LinearCongruentialGenerator:
    """
    Generador de números pseudoaleatorios mediante el método congruencial lineal.
    Parámetros clásicos: a=1103515245, c=12345, m=32768
    """
    def __init__(self, a=1103515245, c=12345, m=32768):
        """
        Inicializa el generador con una semilla.
        Si no se provee semilla, se usa el tiempo actual.
        """
        seed = int(time.time())
        self.seed = seed
        self.a = a
        self.c = c
        self.m = m
        self.current = seed

    def next(self):
        """Genera el siguiente número entero en el rango [0, m-1]"""
        self.current = (self.a * self.current + self.c) % self.m
        return self.current

    def random(self):
        """Genera un float en el rango [0.0, 1.0)"""
        return self.next() / self.m

    def randint(self, low, high):
        """
        Genera un entero en el rango [low, high] (inclusive ambos extremos).
        """
        if low > high:
            raise ValueError("low debe ser menor o igual a high")
        # Genera un número en [0, 1) y lo escala al rango deseado
        r = self.random()
        return low + int(r * (high - low + 1))

    def uniform(self, low, high):
        """Genera un float en el rango [low, high]"""
        return low + self.random() * (high - low)