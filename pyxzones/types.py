from dataclasses import dataclass, field

@dataclass
class Zone():
    x: int
    y: int
    width: int
    height: int
    orientation: str

    def check(self, x, y):
        return (self.x <= x <= self.x + self.width) and (self.y <= y <= self.y + self.height)

@dataclass
class MergeZone(Zone):
    zones: tuple[Zone, ...] = field(init=False)
    surface: Zone           = field(init=False)

@dataclass
class WorkArea():
    x: int
    y: int
    width: int
    height: int
