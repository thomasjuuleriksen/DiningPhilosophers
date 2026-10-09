import random
import unittest

from philosopher import Philosopher, State

MAX_EATING = 3
MAX_THINKING = 4


def make_philosopher(seed=0):
    return Philosopher(1, MAX_EATING, MAX_THINKING, rng=random.Random(seed))


def make_hungry(philosopher, appetite):
    philosopher.state = State.HUNGRY
    philosopher.appetite_left = appetite
    philosopher.starvation = 0


class ThinkingTest(unittest.TestCase):
    def test_starts_thinking_within_range(self):
        for seed in range(50):
            philosopher = make_philosopher(seed)
            self.assertIs(philosopher.state, State.THINKING)
            self.assertTrue(1 <= philosopher.think_left <= MAX_THINKING)

    def test_becomes_hungry_after_thinking_with_appetite_in_range(self):
        philosopher = make_philosopher()
        for _ in range(philosopher.think_left):
            self.assertIs(philosopher.state, State.THINKING)
            philosopher.step()
        self.assertIs(philosopher.state, State.HUNGRY)
        self.assertTrue(1 <= philosopher.appetite_left <= 2 * MAX_EATING)
        self.assertEqual(philosopher.starvation, 0)


class StarvationTest(unittest.TestCase):
    def test_survives_exactly_twice_max_eating_cycles(self):
        philosopher = make_philosopher()
        make_hungry(philosopher, appetite=1)
        for _ in range(2 * MAX_EATING):
            philosopher.step()
        self.assertIs(philosopher.state, State.HUNGRY)

    def test_dies_one_cycle_later(self):
        philosopher = make_philosopher()
        make_hungry(philosopher, appetite=1)
        for _ in range(2 * MAX_EATING + 1):
            philosopher.step()
        self.assertIs(philosopher.state, State.DEAD)

    def test_dead_stays_dead(self):
        philosopher = make_philosopher()
        philosopher.state = State.DEAD
        philosopher.step()
        self.assertIs(philosopher.state, State.DEAD)


class MealTest(unittest.TestCase):
    def test_meal_ends_when_eaten_enough(self):
        philosopher = make_philosopher()
        make_hungry(philosopher, appetite=2)
        philosopher.starvation = 4
        philosopher.grant()
        philosopher.step()
        self.assertIs(philosopher.state, State.EATING)
        philosopher.step()
        self.assertIs(philosopher.state, State.THINKING)
        self.assertTrue(1 <= philosopher.think_left <= MAX_THINKING)
        self.assertEqual(philosopher.starvation, 0)

    def test_meal_is_cut_off_after_max_eating_cycles(self):
        philosopher = make_philosopher()
        make_hungry(philosopher, appetite=MAX_EATING + 2)
        philosopher.starvation = 4
        philosopher.grant()
        for _ in range(MAX_EATING):
            self.assertIs(philosopher.state, State.EATING)
            philosopher.step()
        self.assertIs(philosopher.state, State.HUNGRY)
        self.assertEqual(philosopher.appetite_left, 2)
        self.assertEqual(philosopher.starvation, 0)


if __name__ == "__main__":
    unittest.main()
