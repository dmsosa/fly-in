# The strategy is what it is.

# Dividing the project into sections:

## The parser:

Parser reads the configuration file, read line by line and checks syntax errors, key errors. It builds a dictionary that mimics the shape of a Pydantic class called FlyinGraph, Zone and Connection respectively, and their Pydantic models run more complex validation using the pydantic library.

## The graph

This graph has a list of Zones and list of connections, which are vertices and edges respectively, but we used special objects since they have more data attached like max capacity, pointers to their neighbors, and color and name metadata. 

The graph, as usual, is represented with an adjajency list wich is a type of dict[str, list[tuple[str, int]]]. It is a dictionary where each key is a zone id, and it points to a list of possible neighbor and their costs, in a tuple (neigbor.id, neighbor.cost)

Good so far.

## The pathfinder

The pathfinder is responsible of indicating the next best zone to be moved to, verifying neighbor's distances, occupancy, type, and priority. 

It returns the list of neighbors wose distace is less than the current zone's distance (that allow us to discard dead-ends) sorted by their final computed cost.

## The orchestrator

It is going to receive the sorted list of neighbors, iterate over each one and only make the drone wait if none of them is suitable for move (due to zone being fully occupied or connection fully occupied), the orchestrator is responsible of keeping track of connection and zone occupancies, manage the drone states, and storing the movements made.

For the render, one thing to take into account is that the Move class points to a specific Drone (the drone that moved), Zone (the zone the drone moved to) and Connection (the connection the drone passed through). 

Since render is going to render the 2D array of movements after the simulation ended, it has no way of figuring out the coneection name or zone_name only with drone, since the drone's current_zone, origin, target attributes is likely to change.

Also, the capacities that the connection and zone have may change at the end, they are likely to be different since at the end all the drones are suppposed to be in the end zone.

For that reason, taking into account that the only goal for move is to represent an string to be printed in the terminal,why not to initialize it only with static properties, and when needed to be printed in a GUI, we can use the graph to grab the actual Drone, Zone and Connection classes to have access to their metadata.

# I need to remove 