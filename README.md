*This project has been created as part of the 42 curriculum by durisosa.*

# Fly-in

`Fly-in` is a turn-based drone-routing simulator written in Python. It parses a
network of **zones** (vertices) and **connections** (edges), then schedules a
swarm of drones from the shared `start_hub` to the shared `end_hub`, one turn at
a time, while respecting every capacity limit and the special timing of
restricted zones.

The result of a run is a deterministic movement log such as:

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

## Description

Sending a single drone along a shortest path is trivial. The interesting part
begins when many drones share the same bottlenecks:

- every **zone** has a `max_drones` capacity — how many drones may sit in it at
  the same time;
- every **connection** has a `max_link_capacity` — how many drones may traverse
  it during the same turn;
- a **restricted** zone takes **two turns** to enter: one turn to ride the
  connection, one turn to actually step into the zone;
- **priority** zones should be preferred, **blocked** zones can never be used;
- a drone that cannot legally move has to **wait**.

A naive "everyone follows their own shortest path" strategy produces
oversubscribed zones, dead ends and ping-pong loops. The goal of this project is
to build a simulation engine that produces a **valid, deadlock-free schedule**
for as many maps as possible, and to replay it in a readable, colourful way in
the terminal.

### What the program does

1. **Parses** a map file into a validated graph (`FlyinParser` + pydantic
   models).
2. **Pre-computes** the cost-to-go of every zone with a reverse Dijkstra pass
   (`DijkstraPathfinding`), which doubles as the *reachability* test for
   disconnected maps.
3. **Simulates** turn by turn, letting the orchestrator own *all* capacity
   decisions and ask the pathfinder only for a *ranked* list of options
   (`Orchestrator`).
4. **Exports** the result to `output.txt` and **replays** it in the terminal
   with colours and per-turn usage statistics (`TerminalGui`).

### Feature list

- Full input-file parser with rich validation and helpful error messages.
- Distance-first neighbour ranking (dead ends ranked last, never chosen).
- Zone-capacity and link-capacity enforcement that can never be exceeded.
- Two-turn restricted-zone crossings with a correct in-flight representation.
- Anti ping-pong via a bounded per-drone "recently visited" memory.
- Deadlock detection: a run fails fast with a clear error instead of hanging.
- **Disconnected-map detection**: a goal with no route is refused before turn 1
  (naming every zone without a path), and stray islands only produce a warning.
- Interactive map-selection menu and a confirmation screen.
- Colourised terminal replay with per-turn zone and connection usage.
- A pytest suite (145+ tests) covering models, parser, pathfinding, the
  scheduler and every shipped map end to end.

## Instructions

### Requirements

- **Python ≥ 3.10**
- **Poetry** (recommended) or `pip`
- A terminal that supports ANSI escape codes for the coloured replay (the
  program degrades gracefully to plain text when it does not).

### Installation

With Poetry (recommended):

```bash
make install          # poetry install
```

or manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install "blessed>=1.50,<2.0" "pydantic>=2.13,<3.0" "pytest>=9.1,<10.0"
```

### Running

From the repository root:

```bash
# Interactive: pick the map from the menu
make run

# Non-interactive: open a specific map directly
python3 main.py maps/easy/01_linear_path.txt
# or
make run MAP=maps/hard/03_ultimate_challenge.txt
```

After the run the schedule is written to `output.txt` in the working directory
and replayed in the terminal.

### Testing and linting

```bash
make test            # pytest (requires an active virtualenv)
make lint            # flake8 + mypy
make lint-strict     # mypy --strict
make clean           # remove caches
```

### Project layout

```text
.
├── main.py                     # entry point (menu -> parse -> run -> replay)
├── error/                      # FlyinError, FlyinParseError, FlyinUnreachableError
├── model/
│   ├── graph.py                # Zone, Connection, FlyinGraph (pydantic)
│   ├── drone.py                # Drone state + bounded visited memory
│   └── constants.py
├── parser/                     # line-by-line parser for the map format
├── pathfinding/dijkstra.py     # reverse Dijkstra, ranking, reachability
├── orchestrator/
│   ├── orchestrator.py         # turn loop, scheduling, Move, export
│   └── reservation_table.py    # zone/link capacity bookkeeping
├── gui/                        # terminal printers, colours, replay
├── menu/                       # interactive menu (map selection, confirm)
├── maps/                       # easy / medium / hard / challenger map files
└── tests/                      # pytest suite
```

## Input format

A map is a plain UTF-8 text file. Blank lines and lines whose first
non-space character is `#` are ignored. Every other line is
`key: payload`.

| Key | Payload | Notes |
| --- | --- | --- |
| `nb_drones` | `<int>` | **Mandatory, must be the first statement.** Number of drones. |
| `start_hub` | `name x y [metadata]` | Exactly one. Unlimited capacity. |
| `end_hub` | `name x y [metadata]` | Exactly one. Unlimited capacity. |
| `hub` | `name x y [metadata]` | Any number of intermediate zones. |
| `connection` | `a-b [max_link_capacity=N]` | Undirected edge between two existing zones. |

**Zone metadata** (inside `[...]`, space separated):

| Token | Meaning | Default |
| --- | --- | --- |
| `zone=normal` | cost 1, one turn to enter | `normal` |
| `zone=priority` | cost 0.5, preferred | |
| `zone=restricted` | cost 2, **two turns to enter** | |
| `zone=blocked` | never traversable | |
| `max_drones=N` | simultaneous capacity | `1` |
| `color=<name>` | colour used by the terminal replay | none |

**Connection metadata:**

| Token | Meaning | Default |
| --- | --- | --- |
| `max_link_capacity=N` | drones allowed on the edge per turn | `1` |

Zone names may not contain spaces or dashes (`-`), because dashes separate the
two ends of a connection. A graph is rejected if two zones share a name or a
coordinate, if a connection is duplicated, self-referencing or points at an
unknown zone, or if a mandatory field is missing.

### Minimal example

```text
# maps/easy/01_linear_path.txt
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

## Output format

The simulation produces **one line per turn**. Each line lists the moves of
that turn, separated by a single space:

- a **normal / priority** landing is `D<id>-<zone>`;
- a **restricted** crossing spans two turns and is printed as
  `D<id>-<origin>-<destination>` on the first turn and `D<id>-<destination>` on
  the turn it lands.

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

The same content is written to `output.txt` and replayed on screen.

## Algorithm & implementation strategy

The design follows one rule: **the drone is passive, the orchestrator owns every
decision.** A `Drone` only knows where it is, what it is heading to and which
zones it recently visited. All capacity logic lives in the orchestrator and its
`ReservationTable`. This keeps the tricky part (conflict resolution) in one
place and makes the rest easy to reason about and test.

### 1. Parsing and validation

The parser reads the file line by line, converts each line into a *plain
dictionary*, and hands everything to pydantic models at the end. Splitting the
work this way means syntax errors are reported by the parser and semantic errors
(duplicate names, unknown zones, self-connections…) are reported by the models,
each with a precise message. Two indexes are built once when the graph is
created:

- `zone_name -> Zone`, for O(1) lookups;
- sorted `(zone_a, zone_b) -> Connection`, so `get_connection("a", "b")` and
  `get_connection("b", "a")` return the *same* object. This canonical key is
  what makes per-turn link accounting order-independent.

### 2. Distance map (reverse Dijkstra)

`DijkstraPathfinding.__init__` runs a Dijkstra pass **from the end zone
backwards** over the undirected graph. The resulting `distance_map` stores, for
every reachable zone, the minimum total cost to reach the goal, where each zone
contributes its `static_cost` (`normal = 1`, `priority = 0.5`,
`restricted = 2`, `blocked = ∞`). Unreachable or blocked zones stay at
`inf`.

The orchestrator never asks "give me one path". It asks for the **ranked
neighbour list** (`find_best_zones`), sorted by:

1. distance to the goal (primary key → the head of the list lies on a shortest
   path);
2. current occupancy (spreads drones instead of stacking them);
3. zone name (deterministic tie-break).

Dead ends (`inf`) are kept **last** instead of being removed, so the
orchestrator can see all options; the strict-progress rule (below) makes sure
they are never taken.

The pathfinder keeps **no edge list of its own**: every neighbour lookup goes
through `graph.get_neighbors()`, so the graph stays the single source of truth
for the topology (no duplicated adjacency structure to keep in sync).

Because the pass runs backwards over an *undirected* graph, a zone without a
finite cost-to-go is exactly a zone in another connected component. Two small
queries expose that:

- `is_end_reachable(start=None)` — does the start hub have a route to the goal?
- `unreachable_zones()` — sorted names of every non-blocked zone with no route.

`Orchestrator.run_orchestra()` calls the first one **before the first turn**
and raises `FlyinUnreachableError` naming the hubs and the stranded zones, and
`main.py` catches it to send the user back to the map selector instead of
dumping a traceback. On a *solvable* map the same `unreachable_zones()` query
only produces a warning on `stderr`, because islands can never take part in a
delivery anyway.

### 3. The orchestrator turn loop

Each call to `next_turn()` runs two phases:

**Phase 1 — land in-flight drones.** A drone crossing a restricted link has
`state = FLYIN`. Its `wait_count` is incremented and, once the crossing is
complete, the orchestrator checks the destination zone one more time. If it is
full the drone keeps holding the link and tries again next turn; otherwise it
lands (`_land`) and releases the connection.

*Landing always happens before new departures.* This is what lets a drone that
was blocking a bottleneck move out during the same turn that another drone
wants to move in.

### 3b. Choosing the next zone (`_choose_next`)

For a stopped drone the orchestrator asks the pathfinder for the **ranked**
neighbour list and keeps every candidate that

1. **strictly lowers the cost-to-go** (`candidate_distance < current_distance`).
   Equal-distance "sideways" moves are rejected on purpose: waiting for the
   cheapest neighbour to free up is always better than drifting onto a branch
   that does not bring the drone closer. This single rule is what makes
   ping-pong impossible.
2. has a **free zone slot** (`ReservationTable.is_zone_available`), and
3. has a **free link slot** (`ReservationTable.is_link_available`).

Among the surviving candidates of the best distance tier it prefers a zone the
drone **has not visited recently** (`Drone.last_visited`, a bounded
`deque(maxlen=3)`), and otherwise falls back to the first one. The visited
memory is a *preference*, never a hard ban — a drone that already knows every
legal option is still allowed to take one, so it can never be stranded just
because of its own memory.

If no candidate survives, the drone moves to `DroneState.WAIT` and simply loses
its turn; nothing else changes.

### 4. Capacity enforcement (`ReservationTable`)

Capacity is enforced with two different notions of "time":

- **Zones are persistent.** `zone.drone_count` is the live number of drones
  sitting there. A drone holds its slot from the turn it enters until the turn
  it leaves. A zone is available when `drone_count < max_drones`.
- **Links are per-turn.** A normal hop finishes within the same turn, so it is
  recorded in a per-turn ledger (`_link_hops`). A restricted crossing lasts two
  turns and is therefore tracked by the persistent `connection.drone_count`.
  A link is available when
  `connection.drone_count + hops_this_turn < max_link_capacity`.

The two counters are deliberately kept apart so a restricted crossing is
**never counted twice**. At the end of every turn `record_turn` takes a snapshot
of the live state (including drones that simply stayed put) into
`zone_occupancy` / `link_occupancy`; that snapshot is what the GUI reads.

### 5. Restricted zones and the in-flight move

When the chosen zone is restricted, the drone does **not** land immediately.
Instead it:

1. releases its current zone,
2. increments `connection.drone_count`,
3. clears `current_zone`, sets `target` and switches to `DroneState.FLYIN`,
4. emits the two-end move `D<id>-<origin>-<destination>`.

On the following turn Phase 1 lands it and emits `D<id>-<destination>`. Because
the link is held by `connection.drone_count` during the whole crossing, no other
drone can use that connection in the meantime.

### 6. Deadlock freedom and fail-fast behaviour

Because every accepted move strictly decreases the cost-to-go, a drone can never
bounce between two zones. More strongly, a correct (non-deadlocked) schedule is
always possible for reachable maps: among the drones that are not delivered,
take the one with the smallest cost-to-go. The optimal neighbour that Dijkstra
relaxed into it has an even smaller cost-to-go, so it can only be occupied by an
already-delivered drone — and delivered drones sit in the unlimited end hub.
That neighbour is therefore either free or a start/end hub, so the minimum
drone can always advance.

Three guards turn a broken run into a clear error instead of an infinite loop:

- `run_orchestra` refuses an **unsolvable map** on turn 0 with
  `FlyinUnreachableError("Unreachable goal: no path from 'start' to 'goal'.
  Zones without a route: …")` — a disconnected graph, or a route that only
  exists through `blocked` zones;
- it fails fast with `FlyinError("Deadlock detected: every drone is
  waiting.")` when a turn produces **no move at all**;
- a hard ceiling (`4 × zones × drones + 50` turns) catches any oscillation.

The unreachable check is what makes the impossible-map case honest: the
message says *why* the map has no solution instead of blaming the schedule,
and no `output.txt` is written for a run that never happened.

### 7. Complexity

Let `Z` be the number of zones, `E` the number of connections and `D` the number
of drones.

- Graph building and the Dijkstra map: `O((Z + E) log Z)`, done once.
- One turn: at most one `_choose_next` per stopped drone. Each call scans that
  drone's degree and sorts it, so a turn is bounded by
  `O(D · (deg log deg))`; in practice the ranked lists are tiny.
- Memory: `O(V + E)` for the graph plus O(turns) for the replay history.

## Visual representation

The user experience is split into three stages, all driven from `main.py`.

### 1. Interactive map menu (`menu/`)

On start-up (without a CLI argument) the program prints a presentation banner
and opens a keyboard-driven menu listing the map files found in the repository.
The user navigates with the keys shown on screen and confirms with Enter. This
removes the need to remember any map path.

### 2. Map confirmation screen

Before anything is simulated, `FlyinGui.confirm_map_file` shows a framed
confirmation panel that recalls which map was loaded and lets the user confirm
(start the run), go back to the menu, or quit. This prevents the most common
mistake — running the wrong map and waiting for a long simulation.

### 4. Colourised terminal replay (`TerminalGui`)

After a run, `TerminalGui.print_history()` replays the schedule turn by turn.
For each turn it prints:

1. a centred ` Turn NN ` banner;
2. the moves of the turn, sorted by drone id, with each zone name coloured with
   the `color=` declared in the map (restricted crossings show both endpoints);
3. a **Zone usage** block listing every zone that is occupied during that turn,
   as `current/capacity` (unlimited hubs show `inf`);
4. a **Connection usage** block listing every connection in use, as
   `drones_this_turn/max_link_capacity`.

This is where the visualisation earns its keep: instead of reading a wall of
`D3-zone` tokens, you can *see* the bottleneck behave — a capacity-1 gate filling
to `1/1`, a drone waiting several turns, then the pipeline draining turn by turn.
Zones and links that are not used during a turn are omitted to keep the output
focused. ANSI colours are detected at runtime (`supports_ansi`) and skipped when
stdout is not a real terminal or `NO_COLOR` is set, so piping the output to a
file stays clean.

## Example input and expected output

### Example 1 — a linear path

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

Every intermediate zone holds a single drone, so the two drones travel in a
pipeline. Expected output (`output.txt`):

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

### Example output for a restricted crossing

Input:

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: tunnel 1 0 [color=blue zone=restricted]
end_hub: goal 2 0 [color=red]

connection: start-tunnel [max_link_capacity=1]
connection: tunnel-goal [max_link_capacity=1]
```

Expected output — note the two-turn crossing (`D1-start-tunnel` then `D1-tunnel`)
and that the second drone only starts once the tunnel is free:

```text
D1-start-tunnel
D1-tunnel
D1-goal D2-start-tunnel
D2-tunnel
D2-goal
```

## Testing

```bash
poetry run pytest          # or: make test
```

The suite is organised by layer:

- `tests/model/` — `Zone`, `Connection`, `FlyinGraph`, `Drone` semantics
  (costs, identity, capacity, bounded memory).
- `tests/parser/` — the line parser, including malformed inputs.
- `tests/pathfinding/` — the distance map, the ranked-neighbour invariants
  and the reachability queries (`is_end_reachable`, `unreachable_zones`).
- `tests/orchestrator/` — per-turn behaviour: move formatting, restricted
  crossings, capacity limits, anti-ping-pong and deadlock reporting.
- `tests/orchestrator/test_disconnected.py` — unsolvable maps are refused on
  turn 0 (`FlyinUnreachableError`), while a solvable map with disconnected
  islands still delivers 100 %.
- `tests/test_maps_integration.py` — runs **every** file in `maps/` through the
  full pipeline and asserts 100 % delivery plus a well-formed `output.txt`.

## Resources

### Classic references

- **Dijkstra's algorithm** —
  [Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) and
  E. W. Dijkstra, *A note on two problems in connexion with graphs* (1959).
- **Python `heapq`** —
  [docs.python.org/3/library/heapq.html](https://docs.python.org/3/library/heapq.html)
- **Pydantic v2** (data validation) —
  [docs.pydantic.dev](https://docs.pydantic.dev/)
- **pytest** —
  [docs.pytest.org](https://docs.pytest.org/)
- **`blessed`** (terminal handling) —
  [github.com/jquast/blessed](https://github.com/jquast/blessed)
- **ANSI escape codes** —
  [Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code)
- The project subject *Fly-in* of the 42 curriculum.
- Bundled map documentation: [`maps/README.md`](maps/README.md).

### How AI was used

AI (an LLM coding assistant) was used as a **pair-programming and review tool**,
not as a source of design decisions:

- **Debugging:** diagnosing the capacity bug in which a restricted crossing was
  counted both in `connection.drone_count` and in the per-turn link ledger,
  which made a single drone read as `2/1` on a capacity-1 link.
- **Tests:** drafting the pytest fixtures and cases, and rewriting tests to match
  the final API (`add_last_visited` instead of `remember`).
- **Documentation:** structuring and wording this README, and checking it
  against the subject's required sections.

All architectural choices — the orchestrator-owns-capacity design, the
distance-first ranking, the strict-progress anti-ping-pong rule, the two-turn
restricted-crossing representation and the `ReservationTable` split between
persistent zone occupancy and per-turn link usage — were designed and validated
by the author, and every AI suggestion was reviewed, run against the test suite
and adapted before being kept.

## Technical choices

- **Pydantic models** give parsing/validation for free and make the invariants
  (unique names/coordinates, positive capacities, no self-connections)
  explicit and testable.
- **Canonical sorted connection keys** avoid `frozenset` allocations and make
  `(A, B)` and `(B, A)` the same edge everywhere.
- **Snapshot-based usage reporting** keeps the simulation's hot path (boolean
  availability checks) independent from the reporting path (per-turn
  snapshots), so the GUI can be rich without slowing the scheduler down.
- **Fail fast on deadlock** turns a would-be infinite loop into a clear,
  actionable error.
- **Reachability as a query, not a second search** — the reverse distance map
  already tells whether the start hub can reach the goal, so detecting a
  disconnected graph costs nothing extra (no duplicate Dijkstra pass).

## Known limitations / roadmap

- The animated **grid renderer** (`gui/gui.py`, `gui/gui_ascii.py`) is still
  work in progress; the shipped, fully working replay is the coloured
  `TerminalGui`.
- The scheduler is a greedy, distance-first heuristic. It always finds a valid
  schedule for the shipped maps (and beats the challenger benchmark of 45 turns
  with 43), but it does not attempt to prove global optimality of the total turn
  count.


# October 21.

## Displayin into the temrinal with Pygame

Pygame has a loop which runs, you always need to d pygme.init()  and is a god practice to do conditional imports handling FileIMport Error, and specify which packages are missing  into m project.

since it has its own loops, my idea is that it can rint a history of movements and the while is going to run until the lastmovement is animated.

how to animate a movement, I dont know, and I part rom the base that it  can be printed just by knowing the coordinates.

Step 1: how to draw a graph.

to draw a graph we need to convert the abstract x and y coordinates of each node to a coordinate into the display screen of pygame it tarts always from the top-left corner (that is the 0,0 coordinate off pygame screen) and I can center it to do OFFSET_X = WIDTH // 2 and same for the Y axis.

But how to add a padding ?

width - padding * 2

and how big a zone is going to be ?

Excellent article about animations and what are frames in game development:

Games inherited this term from animation, film, and video.

There, a "frame" is one still image in the sequence. By playing lots of frames in rapid succession, we create the illusion of motion.

See this strip of 35 mm film from the Museum of Obsolete Media. In it, we can see three consecutive frames of a Spider-Man movie.

3 frames of a film

The framerate of a piece of animation/film/video is a measure of how quickly we move from one frame to another. Common values you'll see are 24, 30, or 60 frames per second - that's where the "FPS" abbreviation comes from. In an animation running at 24 fps, 24 different frames (pictures) are displayed for each one second of playback time.

So, at a particular framerate, we can also think of one "frame" as a measure of time - say 1/24th of a second for a 24 fps animation.

All of this carries over to games - the difference is that we typically have to create each image a fraction of a second before it's displayed, rather than just playing back an already-existing image sequence. That includes both the actual work of drawing, and the work to update the internal state of the game - like the positions of the characters - so that we know what to draw.

In games we can say...

A rendered frame is one complete image presented to the player's screen.

By rendering and displaying new frames very quickly, games create the illusion of motion.

The frame rate a game is running at is a measure of how many new frames it displays every second - so a 60 fps game is rendering and displaying 60 new images every second.

A frame interval is the span of time between displaying two consecutive frames. For a game running at 60 fps, that's just over 16 milliseconds.

You'll often hear game developers and players call this span of time "a frame" - like when a fighting game player says "this attack takes 5 frames to hit" what they mean is that 5 frame intervals pass between the time the player hits the attack button and when the attack actually does damage - leaving a potential window to interrupt or block the attack.

We'll also sometimes loosely refer to all the work that the game has to do in order to prepare the next rendered frame as "a frame".

So we do use this word to mean a few different but related things. Generally it's pretty clear what's intended based on the context.

Let's dig into Unity's context to see how this applies.

The Unity game engine has a sequence of steps it goes through for each rendered frame it presents to the player's screen. I'll simplify a little here, but you can find the full breakdown in the documentation.

First, the engine reads the player's input since the last time it checked - things like keyboard key presses, mouse movements & clicks, gamepad buttons, sticks, and triggers, anything you can access via the Input class.

Next, the engine ticks forward the game's physics simulation. This involves running all active scripts' FixedUpdate() methods, then integrating movements using the physics engine, then calling any collision-handling methods like OnCollisionEnter() or OnTriggerStay().

It repeats this trio of operations as many times as it needs to for the game simulation to catch up to the current time (up to a limit). So if the game has been running slow and a lot of time has passed since the last physics step, it might have to loop these several times to catch up. But if the game has been running very fast, it can sometimes skip the physics step entirely, because not enough time has passed for a new one.

Third, it calls all Update() methods on scripts.

Fourth, it updates any animations that are currently playing and applies IK fix-ups.

Then it runs any LateUpdate() methods on scripts, to do last-minute fix-ups that need to react to work that happened earlier in the frame interval.

This could be things like moving a camera, label, or selection cursor that needs to exactly follow another game object that moves in Update() or via animation.

Then it renders the scene, producing a new image - a new rendered frame.

It publishes the new frame to the graphics device, to be presented to the player's screen.

If VSync is enabled, the game waits until the next time the screen is ready for a new image before starting over at 1.

Otherwise, it jumps right back to 1 and does it all again - possibly going faster than the screen can display images. This means that it draws some rendered frames that the player might never see in full - they might get skipped entirely, or get seen partially because they got sent to the screen halfway through a repaint, creating an artifact called "tearing".

So, looking at all the work done during a frame interval, to produce one rendered frame, we can see that all of these statements are true:

Update() is called every frame - Unity Document says

Yes, the Update() method is called on every active script instance, for every frame interval, before drawing each rendered frame. Update() is never skipped (unlike FixedUpdate() for example).

Update() is called during a frame - Some People Says

Et rappelez-vouz: aujourd'hui on a trouve le systeme D pour se debrouiller! 
# Resources

## about fps and pygame basics
https://gamedev.stackexchange.com/questions/174718/what-is-a-frame-and-frame-per-second

https://stackoverflow.com/questions/79978006/how-to-make-two-structs-to-share-the-same-data-in-c/79978015#79978015
