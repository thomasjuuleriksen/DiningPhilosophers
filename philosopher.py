"""A philosopher: a thread running a small state machine, one step per cycle."""

import random
import threading
from enum import Enum


class State(Enum):
    THINKING = "T"
    HUNGRY = "H"
    EATING = "E"
    DEAD = "D"


class Philosopher(threading.Thread):
    """One philosopher.

    The state machine lives in step() and grant(), which contain no thread or
    timing code, so they can be tested directly. run() only synchronises step()
    with the central loop through a barrier: the central loop releases the
    barrier once to start a cycle's step and once more to wait for its end.
    """

    def __init__(self, number, max_eating_cycles, max_thinking_cycles,
                 barrier=None, rng=None):
        super().__init__(name=f"Philosopher {number}", daemon=True)
        self.number = number
        self.max_eating_cycles = max_eating_cycles
        self.max_thinking_cycles = max_thinking_cycles
        self.barrier = barrier
        self.rng = rng or random.Random()

        self.state = State.THINKING
        self.think_left = self.rng.randint(1, max_thinking_cycles)
        self.appetite_left = 0  # cycles of eating still needed to have eaten enough
        self.meal_left = 0      # cycles left of the meal currently granted
        self.starvation = 0     # hungry cycles without being granted the forks

    def grant(self):
        """The central loop grants the forks: eat for up to max_eating_cycles."""
        self.state = State.EATING
        self.meal_left = self.max_eating_cycles

    def step(self):
        """Advance one cycle."""
        if self.state is State.THINKING:
            self.think_left -= 1
            if self.think_left == 0:
                self.state = State.HUNGRY
                self.appetite_left = self.rng.randint(1, 2 * self.max_eating_cycles)
                self.starvation = 0

        elif self.state is State.HUNGRY:
            # Still hungry in this phase means the forks were not granted.
            self.starvation += 1
            if self.starvation > 2 * self.max_eating_cycles:
                self.state = State.DEAD

        elif self.state is State.EATING:
            self.appetite_left -= 1
            self.meal_left -= 1
            if self.appetite_left == 0:
                # Eaten enough: put down the forks and think.
                self.state = State.THINKING
                self.think_left = self.rng.randint(1, self.max_thinking_cycles)
                self.starvation = 0
            elif self.meal_left == 0:
                # Meal period used up but not done: hungry again next cycle.
                self.state = State.HUNGRY
                self.starvation = 0

    def run(self):
        while True:
            try:
                self.barrier.wait()  # wait for the central loop to start the step
                self.step()
                self.barrier.wait()  # tell the central loop the step is done
            except threading.BrokenBarrierError:
                return
