# Dining Philosophers – Implementation Plan

Based on `md file for dining philosophers.md` (final revision).

## 1. Technology
- Python 3, standard library only (`threading`, `argparse`, `random`, `math`, `time`, `os`, `sys`).
- Text output with ANSI escape codes for colours and cursor control (supported by Windows Terminal / Windows 11 console).

## 2. Settings (command-line arguments)
| Argument | Validation | Meaning |
|---|---|---|
| `--philosophers` | integer > 1 | Number of philosophers (and forks) |
| `--max-eating-cycles` | integer > 1 | Longest single meal |
| `--max-thinking-cycles` | integer > 1 | Longest thinking period |
| `--min-cycle-time` | integer > 0 (seconds) | Minimum duration of one cycle |

Invalid values: print an error message and exit.

## 3. Concepts and data

### Cycle
The unit of time. All durations (thinking, eating, starvation, queue waiting) are counted in cycles. Every cycle lasts at least `min_cycle_time` seconds.

### Philosopher (one thread each)
Numbered 1..N. Neighbours of philosopher `i` are `i-1` and `i+1`, wrapping around (philosopher 1 sits next to philosopher N).

Fields:
- `state`: `THINKING`, `HUNGRY`, `EATING` or `DEAD`
- `think_left`: remaining thinking cycles
- `appetite_left`: remaining cycles of eating needed before he has "eaten enough"
- `meal_left`: remaining cycles of the current granted meal
- `starvation`: number of cycles hungry without having been granted the forks

### Queue
An ordered list (FIFO) of entries `(philosopher, cycles_count)`.

### Forks
Fork `i` lies between philosopher `i` and philosopher `i+1`. It is held by an eating neighbour, otherwise it is free. Fork ownership is derived from the eating philosophers, so it can never be inconsistent.

## 4. Philosopher behaviour (lines 9–13 of the spec)
Executed by each philosopher thread once per cycle:

- **THINKING**: decrement `think_left`. At 0, become `HUNGRY`, draw `appetite_left` at random and reset `starvation` to 0.
- **HUNGRY** (not granted this cycle): increment `starvation`. If `starvation > 2 × max_eating_cycles`, become `DEAD`.
- **EATING**: decrement `appetite_left` and `meal_left`.
  - If `appetite_left == 0` (eaten enough): put down the forks, become `THINKING` with `think_left` = random 1..`max_thinking_cycles`.
  - Else if `meal_left == 0` (meal period used up, not done): put down the forks, become `HUNGRY`. He gets to eat again or is queued in the next cycle.
  - In both cases `starvation` is reset to 0.
- **DEAD**: does nothing.

**Starting state:** every philosopher starts `THINKING` with a random `think_left` of 1..`max_thinking_cycles`.

## 5. Central loop (lines 15–23 of the spec)
Runs in the main thread. Each cycle has these phases:

**Phase A – granting (arbiter):**
1. Build the visiting order. First the philosophers currently in the queue, in queue order (taken from a snapshot of the queue at the start of the cycle), then all other philosophers in numeric order.
2. For each philosopher in that order:
   - **DEAD**: stop the program (see section 7).
   - **EATING or THINKING**: skip to the next philosopher.
   - **HUNGRY**: he is granted the forks if
     - neither neighbour is eating, AND
     - no neighbour is in front of him in the queue with `cycles_count > max_eating_cycles`.

     A hungry philosopher who is not in the queue counts as being behind everyone in it.
     - **Granted**: state becomes `EATING`, `meal_left = max_eating_cycles`. If he was in the queue, he is removed from it.
     - **Not granted**: if he is not already in the queue, he is appended with `cycles_count = 0`.

**Phase B – philosopher step:** All philosopher threads perform their per-cycle behaviour (section 4) in parallel.

**Phase C – bookkeeping:**
1. Increment `cycles_count` of every queue entry by 1 (once per cycle).
2. Render the screen.
3. Sleep for the rest of `min_cycle_time`.

### Thread synchronisation
- A `threading.Barrier(N + 1)` (N philosophers plus the central loop) is used twice per cycle: once to release phase B and once to wait for its completion. Phases A and B therefore never overlap.
- No extra lock is needed: the barrier guarantees that the central loop and the philosopher threads never access the shared state at the same time.
- Dead philosophers' threads keep passing the barrier (doing nothing), so the barrier size never changes.

## 6. Text-based graphical representation (lines 26–37 of the spec)
- **Approach:** a character grid is built each cycle and printed after moving the cursor home (`ESC[H`). This redraws without flicker.
- **Table:** an ellipse of `·` characters, twice as wide as high, to compensate for terminal character proportions. Its size grows with the number of philosophers.
- **Bowl:** a small ASCII bowl in the centre of the table, for example:
  ```
   \___/
  ```
- **Philosophers:** placed evenly at angle `2π·(i−1)/N` just outside the table edge, with their number next to the letter.
  - Hungry: yellow `H` (`ESC[33m`)
  - Eating: green `E` (`ESC[32m`)
  - Thinking: blue `T` (`ESC[34m`)
  - Dead: red `D` (`ESC[31m`)
- **Forks:** `-€`, placed on the table edge.
  - Free fork: at the angle midway between the two neighbouring philosophers.
  - Held fork: moved half the way round towards the philosopher holding it, and out towards the table edge. (Moving it 75 % of the way, as first planned, made the two forks of a philosopher at the side of the table land on the same character cell.)
- **Queue:** shown on a line below the table in queue order, with each entry's `cycles_count`, e.g. `Queue: P3(2)  P5(1)  P1(0)`.
- **Status line:** current cycle number.
- **Windows setup:** at start-up the program enables ANSI processing (`os.system("")`), switches stdout to UTF-8 (needed for `€`) and hides the cursor.

## 7. Program termination
- The program runs indefinitely.
- **Death (line 18):** when the central loop finds a dead philosopher, it renders a final frame (showing the red `D`), prints which philosopher died and in which cycle, and exits.
- **User break (line 39):** Ctrl+C is caught (`KeyboardInterrupt`). The program aborts the barrier so the philosopher threads exit cleanly, then restores colours and cursor and exits.

## 8. File structure
```
DiningPhilosophers/
  main.py            # argument parsing, validation, central loop, termination
  philosopher.py     # Philosopher class: state machine (section 4) + thread loop
  arbiter.py         # queue and granting rule (section 5, phase A) – pure logic, no threads
  renderer.py        # grid drawing, geometry, colours
  tests/
    test_arbiter.py      # granting rule, queue, scenarios, rendering
    test_philosopher.py  # state machine
  docs/
    specification.md     # the original requirements
    plan.md              # this plan
  README.md
```
The granting rule and the philosopher state machine are written as plain functions/methods with no thread or timing code, so they can be unit-tested directly. The threads only wrap them.

## 9. Tests
- **Granting rule:**
  - A philosopher is blocked when a neighbour is eating.
  - He is blocked by a queued neighbour ahead of him with `cycles_count > max_eating_cycles`.
  - He is **not** blocked by a queued neighbour ahead of him with `cycles_count ≤ max_eating_cycles` (overtaking).
  - He is never blocked by a neighbour behind him in the queue.
- **Queue:**
  - Entries are added only once; `cycles_count` is not reset while waiting.
  - Counts increase once per cycle.
  - Granted philosophers are removed.
- **Visiting order:** queued philosophers first, in queue order, then the rest in numeric order.
- **Starvation boundary:** a philosopher survives `2 × max_eating_cycles` hungry cycles and dies after `2 × max_eating_cycles + 1`.
- **Meal:**
  - Ends when appetite is satisfied (→ thinking) or after `max_eating_cycles` (→ hungry).
  - The starvation counter is reset in both cases.
- **Scenarios:** the chain scenario (4 philosophers, all hungry in cycle 1) completes without a death; 2 and 3 philosophers never deadlock.
- **Manual check:** run with 5 philosophers and small cycle values to verify the layout, colours, fork positions and queue line.

## 10. Interpretations of the spec
1. **Appetite (line 11, "a random period"):** drawn at random from 1..`2 × max_eating_cycles` each time a philosopher becomes hungry. This is a fixed internal range, not a setting. A meal (line 21) ends when the appetite is satisfied or after `max_eating_cycles`, whichever comes first.
2. **Starvation (line 12):** a philosopher may wait `2 × max_eating_cycles` full cycles and must be granted the forks in the following cycle at the latest.
3. **"In front of him in the queue" (line 21):** a hungry philosopher not yet in the queue counts as behind everyone in it.
4. **Queue counter (lines 22–23):** `cycles_count` is set to 0 only when the philosopher is first enqueued, and incremented once per cycle after all philosophers have been visited.

## 11. Expected behaviour
- **2 or 3 philosophers:** no deadlock, and no deaths (maximum wait is `2 × max_eating_cycles`). Runs until Ctrl+C.
- **4 or more philosophers:** no deadlock. The overtaking rule prevents the typical waiting chains. Rarer chain patterns can still lead to a death, which stops the program as specified.
