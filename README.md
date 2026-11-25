*This project has been created as part of the 42 curriculum by durisosa.*

# Fly-in

`Fly-in` is a turn-based drone-routing simulator written in Python. It parses a
network of **zones** (vertices) and **connections** (edges), then schedules a
swarm of drones from the shared `start_hub` to the shared `end_hub`, one turn at
a time, while respecting every capacity limit and the special timing of
restricted zones.

A run produces a deterministic movement log, written to `output.txt` and
replayed first in the terminal and then in a pygame window:

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

## Description

Sending one drone along a shortest path is trivial. The interesting part starts
when many drones share the same bottlenecks:

- every **zone** has a `max_drones` capacity — how many drones may sit in it at
  the same time;
- every **connection** has a `max_link_capacity` — how many drones may traverse
  it in the same turn;
- a **restricted** zone takes **two turns** to enter: one turn riding the link,
  one turn landing in the zone;
- **priority** zones are preferred, **blocked** zones can never be used;
- a drone that cannot legally move must **wait** instead of taking an unsafe
  shortcut.

The naive "everyone follows their own shortest path" approach produces
oversubscribed zones, dead ends and ping-pong loops. The goal of this project
is a simulation engine that produces a **valid, deadlock-free schedule**, fails
clearly when a map is unsolvable, and makes the resulting schedule readable.

### What the program does

1. **Parses** a map file into validated pydantic models (`FlyinParser` +
   `model/graph.py`).
2. **Pre-computes** the cost-to-go of every zone with a reverse Dijkstra pass
   (`DijkstraPathfinding`), which doubles as the reachability test.
3. **Simulates** turn by turn. The orchestrator owns *all* capacity decisions
   and only asks the pathfinder for a *ranked* list of options.
4. **Exports** the schedule to `output.txt`.
5. **Replays** it with ANSI colours and per-turn usage statistics in the
   terminal (`TerminalGui`), then with an interactive animated map in pygame
   (`FlyinPygameGui`). The terminal replay always runs before the pygame one.

### Feature list

- Full map parser with rich validation and precise error messages.
- Distance-first neighbour ranking; dead ends ranked last, never chosen.
- Zone-capacity and link-capacity enforcement that cannot be exceeded.
- Two-turn restricted crossings with a correct in-flight representation.
- Anti ping-pong via strict progress plus a bounded per-drone visit memory.
- Deadlock detection: fail fast with a clear error instead of hanging.
- Disconnected-map detection: an unreachable goal is refused on turn 0, naming
  every stranded zone; stray islands on a solvable map only produce a warning.
- Interactive map-selection menu and confirmation screen.
- Colourised terminal replay with per-turn zone and connection usage.
- Animated pygame replay with a clickable playback HUD.
- **219 tests** covering models, parser, pathfinding, scheduler, GUI and every
  shipped map end to end.

## Instructions

There is no compilation step: this is a pure Python project.

### Requirements

- **Python ≥ 3.10**
- **Poetry** (recommended) or `pip` to install dependencies
- `blessed`, `pydantic`, `pygame` (runtime) and `pytest` (tests)
- A terminal with ANSI support for the coloured replay; output is automatically
  plain text when stdout is not a TTY or `NO_COLOR` is set.

### Installation

With Poetry (recommended):

```bash
make install          # poetry install
source "$(poetry env activate)"
```

or manually in a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install "blessed>=1.50,<2.0" "pydantic>=2.13,<3.0" \
            "pygame>=2.6,<3.0" "pytest>=9.1,<10.0"
```

All pinned versions are in `pyproject.toml` and `poetry.lock`.

### Running

From the repository root:

```bash
# Interactive: pick the map from the menu
make run

# Non-interactive: run a specific map directly
poetry run python3 main.py maps/easy/01_linear_path.txt
# or
make run MAP=maps/hard/02_capacity_hell.txt
```

CLI options:

| Option | Meaning |
| --- | --- |
| `map` or `-m`, `--map` | Path to a map text file (skips the selection menu) |
| `-g`, `--gui` / `--no-gui` | Enable / disable the pygame window (enabled by default) |
| `-c`, `--color` | Enable coloured terminal metrics |

After the run, `output.txt` is rewritten in the working directory, the
terminal replay is printed, and — unless `--no-gui` was passed — the pygame
window opens with the animated replay. Use `--no-gui` in scripts and CI.

### Testing and linting

```bash
poetry run pytest -q       # 219 tests; also: make test inside an active venv
make lint                  # flake8 + mypy
make lint-strict           # mypy --strict
make clean                 # remove caches
```

### Project layout

```text
.
├── main.py                     # entry point: menu -> parse -> run -> replay
├── error/                      # FlyinError, FlyinParseError, FlyinUnreachableError
├── model/
│   ├── graph.py                # Zone, Connection, FlyinGraph (pydantic)
│   ├── drone.py                # Drone state + bounded visit memory
│   └── constants.py
├── parser/                     # line-by-line parser and metadata parsing
├── pathfinding/dijkstra.py     # reverse Dijkstra, ranking, reachability
├── orchestrator/
│   ├── orchestrator.py         # turn loop, scheduling, Move, export
│   └── reservation_table.py    # zone/link capacity bookkeeping
├── gui/
│   ├── terminal_gui.py         # coloured terminal replay
│   ├── pygame_gui.py           # animated map + playback HUD
│   ├── game_loop.py            # pure clock/command state machine
│   ├── printers.py             # colours, menus and usage tables
│   └── constants.py            # palette used by the pygame map
├── menu/                       # map selection, confirmation, UI configuration
├── static/RobotoMono.ttf       # bundled font for the pygame GUI
├── maps/                       # easy / medium / hard / challenger maps
├── output.txt                  # last generated schedule
└── tests/                      # pytest suite (including headless GUI tests)
```

## Input format

A map is a plain UTF-8 text file. Blank lines and lines whose first non-space
character is `#` are ignored. Every other line is `key: payload`.

| Key | Payload | Notes |
| --- | --- | --- |
| `nb_drones` | `<int>` | Mandatory, must be the first statement |
| `start_hub` | `name x y [metadata]` | Exactly one, unlimited capacity |
| `end_hub` | `name x y [metadata]` | Exactly one, unlimited capacity |
| `hub` | `name x y [metadata]` | Any number of intermediate zones |
| `connection` | `a-b [max_link_capacity=N]` | Undirected edge between existing zones |

Zone metadata (inside `[...]`, space separated):

| Token | Meaning | Default |
| --- | --- | --- |
| `zone=normal` | cost 1, one turn to enter | `normal` |
| `zone=priority` | cost 0.5, preferred | |
| `zone=restricted` | cost 2, **two turns to enter** | |
| `zone=blocked` | never traversable | |
| `max_drones=N` | simultaneous capacity | `1` |
| `color=<name>` | colour used by both GUIs | none |

Connection metadata:

| Token | Meaning | Default |
| --- | --- | --- |
| `max_link_capacity=N` | drones allowed on the edge per turn | `1` |

Zone names may not contain spaces or dashes (`-`), because dashes separate the
two ends of a connection. A graph is rejected if two zones share a name or a
coordinate, if a connection is duplicated, self-referencing or points at an
unknown zone, or if a mandatory field is missing. See `maps/README.md` for the
bundled map documentation.

## Algorithm choices and implementation strategy

The main design rule is: **the drone is passive, the orchestrator owns every
decision.** A `Drone` only knows where it is, where it is heading and which
zones it recently visited. All conflict resolution lives in the orchestrator
and its `ReservationTable`, which keeps the difficult part in one place and
makes it directly testable.

### 1. Parsing and validation

The parser reads the file line by line into plain dictionaries and hands them
to pydantic at the end. Syntax errors are reported by the parser; semantic
errors (duplicate names/coordinates, unknown zones, self-connections) are
reported by the models, each with a precise message. Two indexes are built
once: `zone_name -> Zone` for O(1) lookups, and a canonical sorted
`(zone_a, zone_b) -> Connection` key so `(A, B)` and `(B, A)` always denote the
same edge. Availability checks read the real endpoints of a connection, not
the canonical key — the key is only an index.

### 2. Distance map (reverse Dijkstra)

`DijkstraPathfinding.__init__` runs a Dijkstra pass **from the goal backwards**
over the undirected graph (binary heap from `heapq`). `distance_map[z]` is the
minimum total cost to reach the goal from `z`, where a zone contributes its
`static_cost` (`normal = 1`, `priority = 0.5`, `restricted = 2`,
`blocked = ∞`). Unreachable zones stay at `inf`.

The orchestrator never asks for "one path". It asks for the **ranked neighbour
list** (`find_best_zones`), sorted by:

1. distance to the goal (primary key, so the head lies on a shortest path);
2. current occupancy (spreads drones instead of stacking them);
3. zone name (deterministic tie-break).

`inf` neighbours are kept last rather than removed, so the orchestrator can
see every option; the strict-progress rule below prevents them from being
taken. The pathfinder keeps no edge list of its own: every neighbour lookup
goes through `graph.get_neighbors()`, leaving the graph as the single source
of truth for topology.

Because the pass is backwards over an undirected graph, a zone without a
finite cost-to-go is exactly a zone in another connected component. Two
queries expose that: `is_end_reachable()` (checked before turn 1) and
`unreachable_zones()` (sorted stranded names, used for messages). No second
search is needed.

### 3. The orchestrator turn loop

Each turn has two phases.

**Phase 1 — land in-flight drones.** A drone crossing a restricted link is in
`DroneState.FLYIN`. Its `wait_count` increases; once the crossing is complete
the destination is checked again. If it is full, the drone keeps holding the
link and retries next turn; otherwise it lands and releases the connection.
Landing *always* happens before new departures, so a drone blocking a
bottleneck can leave in the same turn another one enters.

**Phase 2 — choose the next zone** (`_choose_next`). For a stopped drone, the
ranked neighbours are filtered to those that:

1. **strictly lower** the cost-to-go (`candidate < current`). Equal-distance
   sideways moves are rejected on purpose: waiting for the cheapest neighbour
   to free up beats drifting onto a branch that does not get closer. This one
   rule makes ping-pong impossible.
2. have a **free zone slot** (`ReservationTable.is_zone_available`), and
3. have a **free link slot** (`ReservationTable.is_link_available`).

Among the best-distance candidates, a zone absent from the drone's bounded
`deque(maxlen=3)` visit memory is preferred. That memory is a *preference*,
never a hard ban, so a drone can never be stranded by its own history. If no
candidate survives, the drone waits and loses its turn.

### 4. Capacity enforcement (`ReservationTable`)

Two different notions of time are used:

- **Zones are persistent.** `zone.drone_count` is the live number of drones
  sitting there. A drone holds its slot from the turn it enters until the turn
  it leaves; a zone is available when `drone_count < max_drones`.
- **Links are per-turn.** A normal hop finishes within its own turn and is
  recorded in `_link_hops`. A restricted crossing lasts two turns and is
  tracked by the persistent `connection.drone_count`. A link is available when
  `connection.drone_count + hops_this_turn < max_link_capacity`.

The two counters are deliberately separate so a restricted crossing is never
counted twice. At the end of every turn, `record_turn()` takes a snapshot of
the live state (including drones that simply stayed put) into
`zone_occupancy` / `link_occupancy`; those snapshots are what the GUIs read.

### 5. Restricted zones and the in-flight move

When the chosen zone is restricted the drone does not land immediately: it
releases its current zone, increments `connection.drone_count`, clears
`current_zone`, sets its target, switches to `FLYIN`, and emits
`D<id>-<origin>-<destination>`. The following turn lands it and emits
`D<id>-<destination>`. The held link prevents any other drone from using that
connection during the crossing.

### 6. Deadlock freedom and fail-fast behaviour

Every accepted move strictly decreases cost-to-go, so a drone cannot bounce
between two zones. For reachable maps a valid schedule always exists: take an
undelivered drone with the smallest cost-to-go; the optimal neighbour that
Dijkstra relaxed into it has an even smaller value, so it can only be occupied
by an already-delivered drone sitting in the unlimited end hub — hence it is
free or a hub, and the minimum drone can always advance.

Three guards turn a broken run into a clear error instead of a hang:

- an unsolvable map is refused on turn 0 with `FlyinUnreachableError`, naming
  the goal and the stranded zones;
- a turn with no move at all raises `FlyinError("Deadlock detected: every
  drone is waiting.")`;
- a hard ceiling of `4 × zones × drones + 50` turns catches any oscillation.

No `output.txt` is written for a run that never happened.

### 7. Complexity

With `Z` zones, `E` connections and `D` drones: graph building and the
distance map are `O((Z + E) log Z)` once; one turn is bounded by
`O(D · deg log deg)` because each stopped drone sorts only its own short
neighbour list; memory is `O(Z + E)` for the graph plus `O(turns)` for replay.

### 8. Technical choices

- **Pydantic models** make invariants (unique names/coordinates, positive
  capacities, no self-connections) explicit and testable.
- **Canonical sorted connection keys** make `(A, B)` and `(B, A)` the same edge
  everywhere without allocating `frozenset`s.
- **Snapshot-based reporting** keeps the scheduler's hot path independent from
  the reporting path, so richer GUIs do not slow the simulation down.
- **Pure replay timeline**: the pygame GUI precomputes one segment per drone
  per turn and derives every position from a single clock value. Seeking,
  pausing and stepping cannot accumulate drift.
- **Fail fast on deadlock** replaces an infinite loop with an actionable error.

## Visual representation

The experience is split into complementary stages, all driven from `main.py`.

### 1. Interactive map menu and confirmation

Without a CLI argument, a keyboard-driven menu lists the map files found in
the repository; navigation keys are shown on screen. A framed confirmation
panel then recalls the selected map before simulating, so running the wrong
map is caught early. Both screens are implemented in `menu/` with `blessed`.

### 2. Colourised terminal replay

`TerminalGui.print_history()` replays one turn at a time:

1. a centred ` Turn NN ` banner;
2. moves sorted by drone id, each zone name coloured with its `color=` from
   the map (restricted crossings show both endpoints);
3. a **Zone usage** block with occupied zones as `current/capacity` (`inf` for
   hubs);
4. a **Connection usage** block with links in use as `drones/max_link_capacity`.

This makes bottlenecks visible as behaviour: a capacity-1 gate reading `1/1`,
a drone waiting several turns, then the pipeline draining. Unused zones and
links are omitted to keep each frame focused. `manual`, `step-by-step`,
`normal` and `fast` playback speeds are selectable in the UI menu.

### 3. Animated pygame replay

After the terminal replay, `FlyinPygameGui.draw_history()` opens a window sized
to 75 % of the desktop. Map coordinates are scaled and centred automatically
in the area above the HUD.

- Zones are circles: their colour comes from `color=`, high-capacity hubs are
  drawn larger, and zones without a declared colour fall back to the palette
  in `gui/constants.py`.
- Connections are lines whose thickness tracks `max_link_capacity`; capacity-1
  links are dashed, wider links solid.
- Drones are light discs with a white rim. When several drones rest in the
  same zone they are spread around a small ring instead of overlapping; a
  drone waiting on a restricted link is drawn *on the link*, at a fraction of
  the segment, so its two-turn crossing is visible.
- One simulation turn lasts one second by default (`turns_per_second`), at
  60 fps. Positions are interpolated linearly between precomputed turn
  endpoints, so movement reads as continuous rather than teleporting.
- The **bottom HUD** shows `Turn X/Y`, a `PLAYING` / `PAUSED` chip and a
  progress bar, plus five clickable buttons with keycaps:

| Button | Keyboard | Effect |
| --- | --- | --- |
| Next step | `→` or `S` | advance one turn and pause |
| Previous step | `←` or `W` | step back to the previous turn and pause |
| Play/Pause | `Space` or `P` | toggle playback |
| Skip | `F` or `End` | jump to the final turn and pause |
| Exit | `Esc` or `Q` | close the replay |

Buttons highlight on hover; `R` resets to turn 0. The window redraws on every
frame, including while paused, so a click or a step updates the picture
immediately. This turns a plain text log into something you can *inspect*:
pause on a congestion point, step back and forth to see who yielded, or skip
straight to the end.

## Example input and expected output

Both examples below were produced by the actual pipeline (parser →
orchestrator → `export_turns()`); reproduce either with
`poetry run python3 main.py <map> --no-gui` and read `output.txt`.

### Example 1 — linear path

Input (`maps/easy/01_linear_path.txt`):

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Each intermediate zone holds one drone, so the two drones form a pipeline.
Expected `output.txt`:

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

### Example 2 — restricted crossing

Input:

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: tunnel 1 0 [color=blue zone=restricted]
end_hub: goal 2 0 [color=red]

connection: start-tunnel [max_link_capacity=1]
connection: tunnel-goal [max_link_capacity=1]
```

Expected `output.txt` — note the two-turn crossing (`D1-start-tunnel` then
`D1-tunnel`) and that the second drone starts only once the link and tunnel
are free:

```text
D1-start-tunnel
D1-tunnel
D1-goal D2-start-tunnel
D2-tunnel
D2-goal
```

## Testing

```bash
poetry run pytest -q
```

The 219 tests are organised by layer:

- `tests/model/` — `Zone`, `Connection`, `FlyinGraph`, `Drone` semantics.
- `tests/parser/` — line parsing, metadata and malformed inputs.
- `tests/pathfinding/` — distance map, ranking invariants and reachability.
- `tests/orchestrator/` — move formatting, restricted crossings, capacity,
  anti-ping-pong, deadlock and reservation ledgers.
- `tests/orchestrator/test_disconnected.py` — unsolvable maps refused on turn
  0; solvable maps with islands still deliver 100 %.
- `tests/gui/` — headless pygame tests for layout, HUD buttons/commands and
  the replay clock (SDL `dummy` video driver, no window shown).
- `tests/test_maps_integration.py` — every file in `maps/` end to end.

## Resources

### Classic references

- **Dijkstra's algorithm** —
  [Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) and
  E. W. Dijkstra, *A note on two problems in connexion with graphs* (1959).
- **Python `heapq`** —
  [docs.python.org/3/library/heapq.html](https://docs.python.org/3/library/heapq.html)
- **Pydantic v2** (data validation) — [docs.pydantic.dev](https://docs.pydantic.dev/)
- **pytest** — [docs.pytest.org](https://docs.pytest.org/)
- **pygame** (window, drawing, events) — [pygame.org/docs](https://www.pygame.org/docs/)
- **`blessed`** (terminal handling) —
  [github.com/jquast/blessed](https://github.com/jquast/blessed)
- **ANSI escape codes** —
  [Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code)
- **Frames, frame rate and game-loop structure** —
  [gamedev.stackexchange.com](https://gamedev.stackexchange.com/questions/174718/what-is-a-frame-and-frame-per-second)
- The 42 curriculum subject *Fly-in*.
- Local documentation: [`maps/README.md`](maps/README.md) and `JOURNAL.md`.

### How AI was used

AI (an LLM coding assistant) was used as a **pair programmer, debugger and
reviewer** on identified parts of the project, not to replace the overall
design:

- **`gui/pygame_gui.py` and `gui/game_loop.py`**: implementing the bottom-bar
  HUD menu (Next / Previous / Play-Pause / Skip / Exit), mouse hit-testing and
  keyboard commands, per-frame rendering while paused, and the pure
  clock-driven replay timeline; keeping co-located drones visible and drawing
  a drone resting on a link during a restricted crossing.
- **`tests/gui/test_pygame_gui.py`**: drafting headless tests and adapting them
  to the `GameLoop` API; **219 tests** now pass.
- **Regression fixes**: `model/graph.py` (`get_neighbors` misused the sorted
  canonical edge key; duplicate-coordinate error message referenced the wrong
  variables), `orchestrator/reservation_table.py` (transient link hops merged
  into the GUI snapshot and zone availability read from that snapshot), and
  `pathfinding/dijkstra.py` (`find_all_paths` capped at `drone_count`).
- **Documentation**: structuring this README and verifying the two example
  schedules by running them through the real pipeline.

All architectural choices — orchestrator-owns-capacity, distance-first
ranking, strict-progress anti-ping-pong, the two-turn crossing representation
and the split between persistent zone occupancy and per-turn link usage — were
designed and validated by the author. Every AI suggestion was reviewed, run
against the test suite and adapted before being kept.

## Known limitations / roadmap

- The scheduler is a greedy, distance-first heuristic. It delivers 100 % on
  every shipped map (43 turns on the challenger benchmark) but does not prove
  global optimality of the total turn count.
- The pygame zone radius is fixed; on very crowded maps several hubs may end
  up close together. The HUD and the terminal usage tables remain the most
  precise way to inspect those cases.
