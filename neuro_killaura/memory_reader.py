"""
Заглушка чтения памяти Minecraft.
В реальной сборке используется pymem / ReadProcessMemory.
"""
import random
import time
from typing import List


class MockEntity:
    def __init__(self, name: str):
        self.name = name
        self.x = random.uniform(-10, 10)
        self.y = 64.0
        self.z = random.uniform(-10, 10)
        self.hp = random.uniform(10.0, 20.0)
        self.armor = random.uniform(0, 20.0)
        self.height = 1.8
        self.vel_x = self.vel_y = self.vel_z = 0.0
        self.screen_x = self.screen_y = 0
        self.screen_w = self.screen_h = 0

    @property
    def pos(self): return (self.x, self.y, self.z)
    @property
    def velocity(self): return (self.vel_x, self.vel_y, self.vel_z)
    @property
    def screen_pos(self): return (self.screen_x, self.screen_y)


class MemoryReader:
    """
    Заглушка — возвращает случайные сущности для тестирования.
    Реальная реализация: pymem + offsets для нужной версии Minecraft.
    """

    def __init__(self, process_name: str = "javaw.exe"):
        self.process_name = process_name
        self._connected = False
        self._demo_entities = [MockEntity(f"Player{i+1}") for i in range(3)]

    def connect(self) -> bool:
        print(f"[Memory] Попытка подключения к {self.process_name}...")
        self._connected = True
        return True

    def get_entities(self) -> List[MockEntity]:
        for e in self._demo_entities:
            e.x += random.uniform(-0.05, 0.05)
            e.z += random.uniform(-0.05, 0.05)
            e.hp = max(1.0, e.hp - random.uniform(0, 0.1))
        return self._demo_entities

    def get_player_pos(self) -> tuple:
        return (0.0, 64.0, 0.0)

    def get_player_angles(self) -> tuple:
        t = time.time()
        return (t * 10.0 % 360.0, 0.0)

    def is_connected(self) -> bool:
        return self._connected
