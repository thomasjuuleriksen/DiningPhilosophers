"""The central loop's granting rule and the queue of hungry philosophers."""

from dataclasses import dataclass

from philosopher import State


@dataclass
class QueueEntry:
    index: int
    cycles_count: int = 0


class Arbiter:
    """Decides which hungry philosophers may take their two forks.

    Philosophers are addressed by index 0..N-1 (philosopher number = index + 1).
    Fork i lies between philosopher i and philosopher i + 1 (wrapping around).
    """

    def __init__(self, philosophers, max_eating_cycles):
        self.philosophers = philosophers
        self.max_eating_cycles = max_eating_cycles
        self.queue = []

    def neighbours(self, index):
        count = len(self.philosophers)
        return (index - 1) % count, (index + 1) % count

    def queue_position(self, index):
        for position, entry in enumerate(self.queue):
            if entry.index == index:
                return position
        return None

    def is_ahead(self, index, other):
        """True if philosopher index is in front of philosopher other in the queue.

        A philosopher who is not in the queue counts as behind everyone in it.
        """
        position = self.queue_position(index)
        if position is None:
            return False
        other_position = self.queue_position(other)
        return other_position is None or position < other_position

    def is_blocked(self, index):
        for neighbour in self.neighbours(index):
            if self.philosophers[neighbour].state is State.EATING:
                return True
            if self.is_ahead(neighbour, index):
                entry = self.queue[self.queue_position(neighbour)]
                if entry.cycles_count > self.max_eating_cycles:
                    return True
        return False

    def visiting_order(self):
        """Queued philosophers first, in queue order, then the rest by number."""
        queued = [entry.index for entry in self.queue]
        others = [i for i in range(len(self.philosophers)) if i not in queued]
        return queued + others

    def grant_round(self):
        """Visit all philosophers once and grant forks where allowed.

        Returns the first dead philosopher found, or None.
        """
        for index in self.visiting_order():
            philosopher = self.philosophers[index]
            if philosopher.state is State.DEAD:
                return philosopher
            if philosopher.state is not State.HUNGRY:
                continue
            position = self.queue_position(index)
            if not self.is_blocked(index):
                philosopher.grant()
                if position is not None:
                    del self.queue[position]
            elif position is None:
                self.queue.append(QueueEntry(index))
        return None

    def end_cycle(self):
        for entry in self.queue:
            entry.cycles_count += 1

    def fork_holder(self, fork):
        """Index of the philosopher holding fork, or None if it is free."""
        for index in (fork, (fork + 1) % len(self.philosophers)):
            if self.philosophers[index].state is State.EATING:
                return index
        return None
