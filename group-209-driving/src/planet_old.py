#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
from enum import IntEnum, unique
from typing import Optional, List, Tuple, Dict

@unique
class Direction(IntEnum):
    """ Directions in shortcut """
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270


Weight = int
"""
Weight of a given path (received from the server)

Value:  -1 if blocked path
        >0 for all other paths
        never 0
"""


class Planet:
    """
    Contains the representation of the map and provides certain functions to manipulate or extend
    it according to the specifications
    """

    def __init__(self):
        """ Initializes the data structure """
        self.paths = {}
        self.known_fields = {}
        self.known_fields_list = []

    def add_path(self, start: Tuple[Tuple[int, int], Direction], target: Tuple[Tuple[int, int], Direction],
                 weight: int):
        """
        Adds a bidirectional path defined between the start and end coordinates to the map and assigns the weight to it

        Example:
            add_path(((0, 3), Direction.NORTH), ((0, 3), Direction.WEST), 1)
        :param start: 2-Tuple
        :param target: 2-Tuple
        :param weight: Integer
        :return: void
        """

        # the keys in this dictionary are the start coordinates of the path (the field)
        # it not only adds the normal path, but also the reverse path

        start_coords = start[0]
        start_direction = start[1] # this is OUTGOING (absolute)

        target_coords = target[0]
        target_direction = target[1] # this is INCOMING (entered_in)




        # ====================== add the normal path ======================
        # if the start coords are not in the dictionary, add them with empty dict
        if start_coords not in self.paths:
            self.paths[start_coords] = {}

        if (self.paths.get(start_coords).get(start_direction) != None) and (self.paths.get(start_coords).get(start_direction) != (target_coords, target_direction, weight)):
            print("(add_path) Path already exists and will be overwritten!", "Coords:", start_coords, "Direction:", start_direction)

        # add the target coords to the dictionary with the weight
        self.paths[start_coords][start_direction] = (target_coords, target_direction, weight)

        if (self.paths.get(start_coords).get(start_direction) == None):
            print("(add_path) Added new path:", "\tStart:", start, "\tTarget:", target, "\tWeight:", weight)




        # ====================== add the reverse path ======================
        # if the target coords are not in the dictionary, add them with empty dict
        if target_coords not in self.paths:
            self.paths[target_coords] = {}

        if (self.paths.get(target_coords).get(target_direction) != None) and (self.paths.get(target_coords).get(target_direction) != (start_coords, start_direction, weight)):
            print("(add_path) Path already exists and will be overwritten!", "Coords:", target_coords, "Direction:", target_direction)

        # add the start coords to the dictionary with the weight
        self.paths[target_coords][target_direction] = (start_coords, start_direction, weight)
        
        if (self.paths.get(target_coords).get(target_direction) == None):
            print("(add_path) Added reverse path:", "\tStart:", target, "\tTarget:", start, "\tWeight:", weight)

        # TODO remove this when not needed for debugging anymore
        for key in self.paths.keys():
            print("(add_path) All known paths from:", key, self.paths[key])


    def get_paths(self) -> Dict[Tuple[int, int], Dict[Direction, Tuple[Tuple[int, int], Direction, Weight]]]:
        """
        Returns all paths

        Example:
            {
                (0, 3): {
                    Direction.NORTH: ((0, 3), Direction.WEST, 1),
                    Direction.EAST: ((1, 3), Direction.WEST, 2),
                    Direction.WEST: ((0, 3), Direction.NORTH, 1)
                },
                (1, 3): {
                    Direction.WEST: ((0, 3), Direction.EAST, 2),
                    ...
                },
                ...
            }
        :return: Dict
        """

        return self.paths


    def shortest_path(self, start: Tuple[int, int], target: Tuple[int, int]) -> Optional[List[Tuple[Tuple[int, int], Direction]]]:
        """
        Returns a shortest path between two nodes

        Examples:
            shortest_path((0,0), (2,2)) returns: [((0, 0), Direction.EAST), ((1, 0), Direction.NORTH)]
            shortest_path((0,0), (1,2)) returns: None
        :param start: 2-Tuple
        :param target: 2-Tuple
        :return: None, List[] or List[Tuple[Tuple[int, int], Direction]]
        """

        # YOUR CODE FOLLOWS (remove pass, please!)
        pass
