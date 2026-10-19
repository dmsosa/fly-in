|  _This project has been created as part
of the 42 curriculum by durisosa_.

# Description

What if you are leading a swarm of drones from an origin coordinate (x, y) and you want to send all of them to the end coordinate (xf, yf) in as less movements as possible? If it were so, it would be enough to just send each drone and change its coordinates one step at the time to follow the shortest path from Origin to the Destination.

But things are more complicated than that, since each zone has some constraints:

Zone:
---> Priority: It indicates its preference over other kind of zones
---> Max_drones: Maximum amount of drones it can hold at the same time

Connections:
---> Max_link_capacity: how many drones can travel through the same connection, this means, how many drones you can send from A to B in the same turn.

Ok, let's say you can do this part well, now let's repeat the parts this project needs to have:

A fully working simulation written in Python, including:
• A parser for the input file format. *<done>*
• A simulation engine respecting movement and zone rules. *--todo 
• A pathfinding algorithm (or multiple) capable of minimizing total turns. *--todo 
• A visual representation system (terminal colors and/or graphical interface). *--todo 
• A terminal or log output that follows the specified format. *--todo 


For me, the challenge in this project is that this is not just a simple find-shortest-path problem, but you actually need to take into account the constraints in each turn before actually moving the drone.

I need an efficient way to
0. Precalculate distance from end to origin,  or vice-versa, to force myself to master heuristics. 
1. Check possible links, discarding restricted zones or dead_ends
2. Check if the next position I pretend to visit is available, and if its link is available. 
A link is available if and only if is current entering drones and current leaving drones are less than its maximum capacity. 
A zone is available if and only if its current drone_count is less than its maximum capacity.
3. That way, I can construct an array of coordinates to follow.

This is what barra does:

He finds all possible paths from each cell to the end

Then when assigning that path to a drone, it starts filtering them, depending on which paths have space available, which have links available, and taking the intersection of both sets to get a list of valid paths.

It also gets the paths that lead to a zone with priority, but it does not calculate costs or uses distances.

it finally chooses the path by getting the first one that was retrieved. Update drones "target", "remaining turns" and current_path fields, so that it is ready to call the _move_to() method again.

This simulators can print when  it is doing something, including when it is "evaluating" a drone to be moved, because it returns some results without losing the state, but is possible to do this without a generator?

For that reason, we need a method called _move_to, which is going to change the drone state from STOP to FLYIN if it can move, or to WAIT if it can not for connection or zone maximum capacity being reached. 

It is obvious that we need a bigger object which provides access to all drones, to all zones, and connections, we will call it Orchestrator. The Orchestrator is in charge of determining if a drone can move, and after each turn it has the method of providing it current state as an output, to be able to print it or write it to a file.

lso, so, since I have some metrics like total+path+cost, which is he cost of each path, I can have a Path object which has a cost, a Path object should have an Origin, Destiny, list of Zones

method path.get_cost() 

for z in self.zones, sum = z.get_cost(). But this would only work if the cost depends on the distance, but if cost depends on occupancy, a path cost can be different from a moment of the iteration to another
 This is the Fly-in project. 

# Developer's forewords

How can I start to implement my drones to be able to code them and start the flying?

Objectiveof the project: desing an efficient drone routing system that navigates multiple autonomous drones from central base to a target location through a network.

- Create a pathfinding algorithm that triggers simultaneous drone movement while respecting some rules.

- Parse a complex map file

- Implement Object Oriented Design 

- graph algorithms
- concurrent pathfinding
- performance optimization
- real-world constraints such as restricted zones, bottlenecks, and deadlock prevention.


# Chapter 1:
Building a simple graph and visualizing it with python

Reading the subject again...

1. while i < nb_drones
start_vertex: Coord
end_vertex: Coord
vertices: Zone

class Zone has:
name
coord: Coord
zone_type: Zone_Type
color: str default "none"

# Parsin Strategy:

1. Parse one line, depending on its type of text, initialize a specific object and its attributes.

2. Parse one line, add to the graph object.

# The Models...

I have written the classes without Pydantic first because I thought the validation process could be simple enough to put inside an __init__ method,
unfortunately (or not) it was not the case.

# Display the menu:

The program starts by allowing the user to interact with a menu that allows you to open an specific file within the current directory. And the parser process each line of the configuration file, to add connections and zones to the graph progressively. 

After the graph is built, I can find the actual solutions for it. 

The simulator.simulate() receives a graph, returns a void.


# Moving strategy:

In order to move all drones, I have a FlyinSimulator class which runs while loop until all drones have reached the end hub.

It iterates through each drone. It moves, so it needs the next_zone's position and also need to know its metadata, for that reason, I use rather directly the Zone class rather than just a tuple[int, int].

When I use the connections, actually? That is to optimize and move more than one drone through the same connection in the same turn.

Also, Drone can have their status, waiting, moving or stopped, and it is going to reflect on the gui.

# Chapter 2:

Sincronizing simulator with the GUI

I want my simulator to:

firts, find all possible paths for each drone, store them in the state

have a method "next_turn" that returns the next movement a drone has done, which is moving to the next cell in their possible paths.

How can I implement this, but with my own simple algorithm that send the drones each time through the next connection which has fewer occupancy?

update the state of my network


for the pathfinding part of my project, I have a orchestrator class, which is going to receive a graph already built by the config.txt parser.

The FlyinOrchestrator class receives a graph, in its init method it sets the folowing fields *they also need to be declared with pdantic*  self._graph = graph
self.drones = self.graph.start_zone.drones


it has a method simulation_turn, which is going to return me a single movement that  a drone decided to do. 

the simulation ends when: orchestrator . check_end() method, which iterates over each of self.drones and returns False if for one drone, Drone.finished() is False

the thing is, I dont know how to make my simulator to dont lose its state, and being able to return each time the next movement that a drone executed, modifying the drones within the graph, and nothing else.
Drone has a method _start_move which modify its state to drone.State.fLYIN, sets its current_zone to None.

there is another pacage pathfinding, which allows me to choose the best path taking into account distance *manhattan distance*

Pathfinder base class has a pathfinderAstar implementation. 
which is the one we are going to focus on, this greedy is going to choose the cheapest zone depending on manhattan distance, , connection usage, sinc

PathfindingDjikstra:

This pathfinding pre-calculates a distanceMap in its init method
after that, the pathfinding has a method find_best_zone(zone) receives a zone and returns the best zone that the drone can access to, taking into account distance, and occupancy costs. It returns a Zone or None, in case there is no best movement, which means all neighbors have a distance bigger than current_zone's distance, or are all of them occupied.


# Chapter 3

## The flow of the program

after the config file has been parsed, I buid a graph out of it, which fields include the total number of rones, the zones and connections (which are other objects). It has a very important method get_zone_by_names(zone_a, zone_b) which is going to find and return a zone in which both zone_a and zone_b are included.

After that, the pathfinding algorithm is initialized with the graph only, it's task is to build a distanceMap from end to finish. Then it uses it to have a find_best_zone method, which returns the zone which less distance from the current_zone. 

Then, the orchestrator is initialized with the given graph and pathfinding

Orchestrator is going to return a 2D list of Moves, which will be used to export the output.txt and the render can also use it to render the graph and its moves graphically.

Orchestrator generates the 2D list of Moves with its method run, which iterates over each drone while NOT all drones have been delivered *Marked with DELIVERED state*, when I take a drone, the first question is to ask which is its zone with less distance to the end, but if I return a single zone from pathfinding, without taking into account occupancies already, I wont be able to pick a zone with bigger distance when other neighbors get  a higher score because of occupancy constraints 

# Chapter 4 - October 14

When a drone moves, the following actions are to be done:

The DRONE itself does not care about occupancy or connection constraints.


1. Set current_zone to None, since the drone is leaving it
2. Set target_zone to the next zone that was found by the pathfinding algorithm
3. Update zone's counts.
4. Update connection's counts.

Taking into account the bonus,  I need to be able to add a flag.
That flag is a boolean, which when set to true
For each turn
For each zone, print its current occupancy.
For each connection, print its max link capacity.


# Chapter 5 - October 14

1. If the pathfinding just suggest the shortest path without taking into account occupancies, the orchestrator is going to reject that movements
2. Now, how to make the orchestrator take care of the occupancy, link usage and at the same time, keep asking the pathfinding to another route if the last one was not available.
3. It is not possible, so if the pathfinding returns me an array of possible zones, I can iterate over them. They need to be ranked, so I keep even the one with lowest score. And the score depends on occupancy, priority and type of zone, preferring NORMAL or PRIORITY ones over RESTRICTED zones.

#  Chapter 6 - October 15

for taking into account more than one one, I need to access my current zone, and then its neighbours.

for n in current_zone.neighbors:
    I want to preverse every node which distance is lower than my current one.

    Let's call that function "get_shorther_nodes"
    once I have the shorther nodes, I filte out the ones whose connection is fully occupied or which zone is occupied itself. Then I want to take the one with less ocupancy, cost = pathfinding.distance_map[neighbor.name] + neighbor.occupancy. 

The pathfinding needs to do the following: take the current zone and find its neighbors. Once it has its neigbors, it is going to  calclate its current score with occupancy, so I need the Zone object itself, not  just its distance


### For this purpose, the tools that my  orchestrator needs to have is:

- A way  to keep track of zone's occupancies
    --- uses the drone.current_zone and current_zone.connections attributes.
- A way to get connection occuppancies.
    --- uses the normalized name of the connection (A, B) and (B,  A) are both equal to (A, B)
    for that, it is going to use the method self.graph.get_connection(zone_a, zone_b), it sorts both strings in a tuple and uses the dictionary self.graph.conn_by_names
    the advantage is that I dont create a frozenset, and is not only a conn_usag dict, but a dict with all connection  information.
- With this two, I can already determine if a zone is fully occupied or not


# Chapter 6 

Printing movements:

If drone moves to  normal zone, the output of the movement MUST be formatted in the following way: 

"D{id}-{targetZone}" 
if movement is to restricted zone: "D{id}-{zoneA}_{zoneB}"

For giving output to the printer, the disavantage of using move 2D array is like printing each move to string, and after the move its details, if I have a snaptshot of what happens in each turn, would be like

In a turn, I have a list of movements, 
a map of zoones and their occupancy at that moment
a map of edges and their occupancy

that would be created by the pathfinder?

then the orchestrator only needs to e 

It turns out that it is, in fact, possible to execute the minimum amount of movements leadin the drones with a greedy behaviour, but, how is it possible to print after each turn of moves, the corresponding zone occupancy and connection usage?

By, after a movement row, D1-dest1 D2-dest2