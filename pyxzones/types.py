class Zone:
    def __init__(self, x, y, width, height) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def check(self, x, y):
        if (self.x <= x <= self.x + self.width) and (
            self.y <= y <= self.y + self.height
        ):
            return True
        return False

    @property
    def corners(self):
        return [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height),
        ]

    def __repr__(self):
        return f"{{x={self.x}, y={self.y}, w={self.width}, h={self.height}}}"


class Coordinates:
    def __init__(self) -> None:
        self.x = []
        self.y = []

    def __getitem__(self, item):
        """returns an (x,y) coordinate"""
        return self.x[item], self.y[item]

    def __iter__(self):
        """iterate over (x,y) coordinates"""
        return zip(self.x, self.y)

    def add(self, x, y):
        self.x.append(x)
        self.y.append(y)

    def clear(self):
        self.x = []
        self.y = []
