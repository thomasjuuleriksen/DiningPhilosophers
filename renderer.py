"""Text-based drawing of the table, the bowl, the philosophers and the forks."""

import math

from philosopher import State

RESET = "\x1b[0m"
COLOURS = {
    State.HUNGRY: "\x1b[33m",    # yellow
    State.EATING: "\x1b[32m",    # green
    State.THINKING: "\x1b[34m",  # blue
    State.DEAD: "\x1b[31m",      # red
}
FORK = "-€"
BOWL = ("\\~~~~~/", " \\___/")
TABLE_EDGE = "·"
FREE_FORK_RADIUS = 0.7  # forks lie on the table, inside its edge
HELD_FORK_RADIUS = 0.85  # a held fork moves out towards its holder ...
HELD_SHIFT = 0.5         # ... and half the way round towards him


class Renderer:
    def __init__(self, count):
        self.count = count
        # Terminal characters are about twice as tall as wide, so the table is
        # an ellipse twice as wide (in columns) as it is high (in rows).
        self.radius_y = max(5, math.ceil(0.8 * count))
        self.radius_x = 2 * self.radius_y
        self.width = 2 * (self.radius_x + 6) + 1
        self.height = 2 * (self.radius_y + 2) + 1
        self.centre_x = self.width // 2
        self.centre_y = self.height // 2

    def seat_angle(self, index):
        """Philosopher 1 sits at the top; the others follow clockwise."""
        return -math.pi / 2 + 2 * math.pi * index / self.count

    def fork_angle(self, fork, holder):
        half_gap = math.pi / self.count
        middle = self.seat_angle(fork) + half_gap
        if holder == fork:
            return middle - HELD_SHIFT * half_gap
        if holder is not None:
            return middle + HELD_SHIFT * half_gap
        return middle

    def point(self, angle, scale, extra_x=0, extra_y=0):
        x = self.centre_x + (self.radius_x * scale + extra_x) * math.cos(angle)
        y = self.centre_y + (self.radius_y * scale + extra_y) * math.sin(angle)
        return round(x), round(y)

    def render(self, arbiter, cycle):
        grid = [[" "] * self.width for _ in range(self.height)]

        def put(x, y, text, colour=None):
            for offset, char in enumerate(text):
                if 0 <= x + offset < self.width and 0 <= y < self.height:
                    grid[y][x + offset] = f"{colour}{char}{RESET}" if colour else char

        steps = 8 * self.radius_x
        for step in range(steps):
            put(*self.point(2 * math.pi * step / steps, 1.0), TABLE_EDGE)

        for row, line in enumerate(BOWL):
            put(self.centre_x - 3, self.centre_y + row, line)

        for fork in range(self.count):
            holder = arbiter.fork_holder(fork)
            radius = FREE_FORK_RADIUS if holder is None else HELD_FORK_RADIUS
            x, y = self.point(self.fork_angle(fork, holder), radius)
            put(x - 1, y, FORK)

        for index, philosopher in enumerate(arbiter.philosophers):
            x, y = self.point(self.seat_angle(index), 1.0, extra_x=4, extra_y=2)
            label = f"{philosopher.state.value}{philosopher.number}"
            x -= len(label) // 2
            put(x, y, label[0], COLOURS[philosopher.state])
            put(x + 1, y, label[1:])

        queue = "  ".join(
            f"P{entry.index + 1}({entry.cycles_count})" for entry in arbiter.queue
        )
        legend = "   ".join(
            f"{COLOURS[state]}{state.value}{RESET} {state.name.lower()}" for state in State
        )
        lines = ["".join(row) for row in grid]
        lines += [
            "",
            f"Cycle: {cycle}",
            f"Queue: {queue or '(empty)'}",
            legend + "      Ctrl+C to stop",
        ]
        # Clear to end of line, so a shorter line fully replaces a longer one.
        return "\n".join(line + "\x1b[K" for line in lines)
