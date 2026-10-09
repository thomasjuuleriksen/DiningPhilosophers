"""Dining philosophers: a central loop grants forks to philosopher threads."""

import argparse
import os
import sys
import threading
import time

from arbiter import Arbiter
from philosopher import Philosopher
from renderer import RESET, Renderer

HOME = "\x1b[H"
CLEAR_SCREEN = "\x1b[2J"
CLEAR_BELOW = "\x1b[J"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"


def integer_above(minimum):
    def parse(text):
        try:
            value = int(text)
        except ValueError:
            raise argparse.ArgumentTypeError(f"'{text}' is not an integer")
        if value <= minimum:
            raise argparse.ArgumentTypeError(f"must be bigger than {minimum}, got {value}")
        return value
    return parse


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(description="Dining philosophers simulation.")
    parser.add_argument("--philosophers", type=integer_above(1), default=5,
                        help="number of philosophers, bigger than 1 (default: 5)")
    parser.add_argument("--max-eating-cycles", type=integer_above(1), default=3,
                        help="longest single meal in cycles, bigger than 1 (default: 3)")
    parser.add_argument("--max-thinking-cycles", type=integer_above(1), default=5,
                        help="longest thinking period in cycles, bigger than 1 (default: 5)")
    parser.add_argument("--min-cycle-time", type=integer_above(0), default=1,
                        help="minimum duration of a cycle in seconds, bigger than 0 (default: 1)")
    return parser.parse_args(argv)


def prepare_terminal():
    os.system("")  # enables ANSI escape codes in the Windows console
    sys.stdout.reconfigure(encoding="utf-8")  # needed for the € of the forks
    sys.stdout.write(CLEAR_SCREEN + HIDE_CURSOR)


def run(args):
    barrier = threading.Barrier(args.philosophers + 1)
    philosophers = [
        Philosopher(index + 1, args.max_eating_cycles, args.max_thinking_cycles, barrier)
        for index in range(args.philosophers)
    ]
    arbiter = Arbiter(philosophers, args.max_eating_cycles)
    renderer = Renderer(args.philosophers)
    for philosopher in philosophers:
        philosopher.start()

    prepare_terminal()
    cycle = 0
    try:
        while True:
            cycle += 1
            started = time.monotonic()

            dead = arbiter.grant_round()
            if dead is not None:
                # He died in the previous cycle's step, already shown on screen.
                print(f"\nPhilosopher {dead.number} died of starvation in cycle {cycle - 1}.")
                return

            barrier.wait()  # let all philosophers take their step
            barrier.wait()  # wait until all of them have finished it
            arbiter.end_cycle()

            sys.stdout.write(HOME + renderer.render(arbiter, cycle) + CLEAR_BELOW)
            sys.stdout.flush()
            time.sleep(max(0.0, args.min_cycle_time - (time.monotonic() - started)))
    except KeyboardInterrupt:
        print(f"\nStopped by user after {cycle} cycles.")
    finally:
        barrier.abort()  # releases the philosopher threads so they exit
        sys.stdout.write(RESET + SHOW_CURSOR)
        sys.stdout.flush()


if __name__ == "__main__":
    run(parse_arguments())
