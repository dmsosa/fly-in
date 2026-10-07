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