# Dining Philosophers

A terminal simulation of the classic dining philosophers problem. Each philosopher is a thread. A central loop decides who may pick up the forks, and the table is drawn in colour in the terminal every cycle.

```
               E1
            ·········
         ···-€    -€ ···
       ··               ··
  H5  ··                 ·· T2
      ·                   ·
      ·      \~~~~~/      ·
      · -€    \___/   -€  ·
      ··                 ··
       ··      -€       ··
         ···         ···
            ·········
       H4              T3

Cycle: 6
Queue: P4(2)
```

## Running it

Requires Python 3.8 or newer and nothing else (standard library only).

```
python main.py
python main.py --philosophers 7 --max-eating-cycles 4 --max-thinking-cycles 6 --min-cycle-time 1
```

| Option | Rule | Default | Meaning |
|---|---|---|---|
| `--philosophers` | integer > 1 | 5 | Number of philosophers (and forks) |
| `--max-eating-cycles` | integer > 1 | 3 | Longest single meal, in cycles |
| `--max-thinking-cycles` | integer > 1 | 5 | Longest thinking period, in cycles |
| `--min-cycle-time` | integer > 0 | 1 | Minimum duration of a cycle, in seconds |

The program runs until a philosopher starves or you press **Ctrl+C**.

Use a terminal that understands ANSI colour codes, such as Windows Terminal, the Windows 11 console or any macOS/Linux terminal.

## What you see

- **Philosophers** sit evenly around the table, each shown with a letter and their number:
  - `H` (yellow): hungry
  - `E` (green): eating
  - `T` (blue): thinking
  - `D` (red): dead
- **Forks** `-€`: a free fork lies midway between two philosophers. A fork that is in use is moved towards the philosopher holding it.
- **Queue:** the hungry philosophers waiting for forks, in order, each with the number of cycles they have been waiting, e.g. `P4(2)`.

## The rules

**Time** is counted in cycles. In each cycle the central loop first hands out forks, then every philosopher thread takes one step.

**A philosopher:**
1. thinks for a random 1 to `max-thinking-cycles` cycles;
2. becomes hungry and needs to eat a random 1 to 2 × `max-eating-cycles` cycles;
3. when granted the forks, eats until he has had enough or for at most `max-eating-cycles` cycles, whichever comes first. If he isn't done, he is hungry again in the next cycle;
4. dies if he goes more than 2 × `max-eating-cycles` cycles without being granted the forks. The counter resets after every meal.

**The central loop** visits the queued philosophers first, in queue order, then all others by number. A hungry philosopher gets both forks if:
- neither neighbour is eating, **and**
- no neighbour who is ahead of him in the queue has waited more than `max-eating-cycles` cycles.

Otherwise he joins the end of the queue, if he isn't in it already.

### Why the rule looks like this

- **Checking that neither neighbour is eating** means a philosopher always takes both forks at once. Nobody holds one fork while waiting for the other, so there is never a deadlock.
- **The queue protects philosophers who have waited long.** A newcomer can't take the forks a long-waiting neighbour needs.
- **The `max-eating-cycles` threshold lets newcomers overtake** a neighbour who can still afford to wait one more meal. Without it, a row of hungry philosophers could form a chain where each one waits for the next. The last one in the chain would then wait for several meals in a row and starve.

## What to expect

- **2 or 3 philosophers:** nobody can ever starve. The longest possible wait is exactly 2 × `max-eating-cycles`. The simulation runs until you stop it.
- **4 or more philosophers:** a death is still possible in a rare pattern. A philosopher becomes hungry while one neighbour is eating and the other neighbour is a protected long-waiter, who in turn waits for someone else. In test runs:
  - With the default settings, this happened only after thousands of cycles, if at all.
  - With long meals and short thinking (for example `--max-eating-cycles 5 --max-thinking-cycles 2`) and 6 or more philosophers, it happened within a few hundred to a few thousand cycles.

## Tests

```
python -m unittest
```

The tests cover the philosopher state machine, the granting rule and the queue, the chain scenario, that 2 and 3 philosophers never starve, that no two neighbours ever eat at the same time, and that every philosopher and fork is drawn.

## Project layout

| File | Contents |
|---|---|
| `main.py` | Command-line options, the central loop and thread synchronisation |
| `philosopher.py` | The philosopher thread and its state machine |
| `arbiter.py` | The queue and the rule for granting forks (pure logic, no threads) |
| `renderer.py` | Drawing the table, bowl, philosophers, forks and queue |
| `tests/` | Unit tests |
| `docs/specification.md` | The original requirements |
| `docs/plan.md` | The implementation plan derived from them |
