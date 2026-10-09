import random
import unittest

from arbiter import Arbiter, QueueEntry
from philosopher import Philosopher, State
from renderer import FORK, Renderer

MAX_EATING = 3
MAX_THINKING = 4


def make_table(count, seed=0):
    rng = random.Random(seed)
    philosophers = [
        Philosopher(index + 1, MAX_EATING, MAX_THINKING, rng=rng) for index in range(count)
    ]
    return philosophers, Arbiter(philosophers, MAX_EATING)


def make_hungry(philosopher, appetite=MAX_EATING):
    philosopher.state = State.HUNGRY
    philosopher.appetite_left = appetite
    philosopher.starvation = 0


def run_cycle(arbiter):
    """One cycle as the central loop runs it, without threads."""
    dead = arbiter.grant_round()
    if dead is None:
        for philosopher in arbiter.philosophers:
            philosopher.step()
        arbiter.end_cycle()
    return dead


class BlockingTest(unittest.TestCase):
    def setUp(self):
        self.philosophers, self.arbiter = make_table(5)

    def test_free_when_neighbours_are_not_eating_or_queued(self):
        self.assertFalse(self.arbiter.is_blocked(2))

    def test_blocked_by_eating_neighbour(self):
        self.philosophers[1].state = State.EATING
        self.assertTrue(self.arbiter.is_blocked(2))

    def test_blocked_by_neighbour_ahead_who_waited_too_long(self):
        self.arbiter.queue = [QueueEntry(1, MAX_EATING + 1), QueueEntry(2, 0)]
        self.assertTrue(self.arbiter.is_blocked(2))

    def test_overtakes_neighbour_ahead_who_can_still_wait(self):
        self.arbiter.queue = [QueueEntry(1, MAX_EATING), QueueEntry(2, 0)]
        self.assertFalse(self.arbiter.is_blocked(2))

    def test_not_queued_counts_as_behind_everyone(self):
        self.arbiter.queue = [QueueEntry(1, MAX_EATING + 1)]
        self.assertTrue(self.arbiter.is_blocked(2))

    def test_never_blocked_by_neighbour_behind(self):
        self.arbiter.queue = [QueueEntry(2, 0), QueueEntry(3, MAX_EATING + 5)]
        self.assertFalse(self.arbiter.is_blocked(2))

    def test_non_neighbour_in_queue_does_not_block(self):
        self.arbiter.queue = [QueueEntry(4, MAX_EATING + 5)]
        self.assertFalse(self.arbiter.is_blocked(2))


class QueueTest(unittest.TestCase):
    def setUp(self):
        self.philosophers, self.arbiter = make_table(5)

    def test_blocked_philosopher_is_enqueued_once_and_count_kept(self):
        self.philosophers[0].state = State.EATING
        self.philosophers[0].meal_left = 10
        self.philosophers[0].appetite_left = 10
        make_hungry(self.philosophers[1])
        for expected_count in range(1, 4):
            run_cycle(self.arbiter)
            self.assertEqual(self.arbiter.queue, [QueueEntry(1, expected_count)])

    def test_granted_philosopher_is_removed_from_queue(self):
        make_hungry(self.philosophers[1])
        self.arbiter.queue = [QueueEntry(1, 2)]
        self.arbiter.grant_round()
        self.assertIs(self.philosophers[1].state, State.EATING)
        self.assertEqual(self.arbiter.queue, [])

    def test_visiting_order_is_queue_first_then_by_number(self):
        self.arbiter.queue = [QueueEntry(3), QueueEntry(1)]
        self.assertEqual(self.arbiter.visiting_order(), [3, 1, 0, 2, 4])

    def test_queued_philosopher_is_served_before_others(self):
        # 0 and 1 are neighbours and both hungry; 1 is queued, so 1 goes first.
        make_hungry(self.philosophers[0])
        make_hungry(self.philosophers[1])
        self.arbiter.queue = [QueueEntry(1, 1)]
        self.arbiter.grant_round()
        self.assertIs(self.philosophers[1].state, State.EATING)
        self.assertIs(self.philosophers[0].state, State.HUNGRY)
        self.assertEqual(self.arbiter.queue, [QueueEntry(0, 0)])

    def test_dead_philosopher_is_reported(self):
        self.philosophers[3].state = State.DEAD
        self.assertIs(self.arbiter.grant_round(), self.philosophers[3])


class ScenarioTest(unittest.TestCase):
    def test_chain_scenario_is_broken_by_overtaking(self):
        # 4 philosophers, all hungry in cycle 1. Without overtaking, P4 would
        # wait behind P3, P2 and P1 and die. With it, P1 and P3 eat at once.
        philosophers, arbiter = make_table(4)
        for philosopher in philosophers:
            make_hungry(philosopher, appetite=MAX_EATING)
        arbiter.grant_round()
        self.assertEqual([p.state for p in philosophers],
                         [State.EATING, State.HUNGRY, State.EATING, State.HUNGRY])
        for philosopher in philosophers:
            philosopher.step()
        arbiter.end_cycle()
        for _ in range(MAX_EATING - 1):
            self.assertIsNone(run_cycle(arbiter))
        arbiter.grant_round()
        self.assertIs(philosophers[1].state, State.EATING)
        self.assertIs(philosophers[3].state, State.EATING)

    def test_two_and_three_philosophers_never_die(self):
        for count in (2, 3):
            for seed in range(20):
                philosophers, arbiter = make_table(count, seed)
                for cycle in range(2000):
                    dead = run_cycle(arbiter)
                    self.assertIsNone(
                        dead, f"{count} philosophers, seed {seed}: death in cycle {cycle}")

    def test_never_two_neighbours_eating(self):
        for count in range(2, 9):
            philosophers, arbiter = make_table(count, seed=count)
            for _ in range(500):
                if run_cycle(arbiter) is not None:
                    break
                for index, philosopher in enumerate(philosophers):
                    if philosopher.state is State.EATING:
                        for neighbour in arbiter.neighbours(index):
                            self.assertIsNot(philosophers[neighbour].state, State.EATING)


class RendererTest(unittest.TestCase):
    def test_every_philosopher_and_fork_is_drawn(self):
        for count in range(2, 16):
            philosophers, arbiter = make_table(count, seed=count)
            for _ in range(5):
                run_cycle(arbiter)
            frame = Renderer(count).render(arbiter, cycle=5)
            self.assertEqual(frame.count(FORK), count, f"{count} philosophers")
            for philosopher in philosophers:
                self.assertIn(f"{philosopher.state.value}\x1b[0m{philosopher.number}", frame)


if __name__ == "__main__":
    unittest.main()
