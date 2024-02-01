from dataclasses import dataclass


@dataclass(frozen=True)
class Zone:
    x: int
    y: int
    width: int
    height: int
    orientation: str

    def check(self, x, y):
        return (self.x <= x <= self.x + self.width) and (self.y <= y <= self.y + self.height)


@dataclass(frozen=True)
class MergeZone(Zone):
    zones: tuple[Zone, ...]
    surface: Zone


@dataclass(frozen=True)
class WorkArea:
    x: int
    y: int
    width: int
    height: int
