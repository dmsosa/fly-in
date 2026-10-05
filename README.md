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

