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

Also, Drone can have their status, waiting, moving or stopped, and it is going to reflect ont he gui.

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

PathfinderAstar:

method find_path() receives a starting_zone,  end_zone, returns an array of zones. 

current_zone = start

while 