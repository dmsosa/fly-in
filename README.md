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
