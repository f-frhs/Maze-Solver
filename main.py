from __future__ import annotations  # for static constructor
import os
import sys
from enum import Enum
from typing import NamedTuple


class EFloor(Enum):
    Normal = 0
    Wall = 1
    Start = 2
    Goal = 3

    def to_char(self) -> chr:
        if (self == EFloor.Normal): return ' '
        elif (self == EFloor.Wall): return '*'
        elif (self == EFloor.Start): return 'o'
        elif (self == EFloor.Goal): return 'x'
        raise ValueError(f"Cannot convert to_char() with self={self}")

    @staticmethod
    def of(c: chr) -> EFloor:
        if c == ' ': return EFloor.Normal
        elif c == '*': return EFloor.Wall
        elif c == 'o': return EFloor.Start
        elif c == 'x': return EFloor.Goal
        raise ValueError("Invalid character: '{}'".format(c))


class Vector2D(NamedTuple):
    x: int
    y: int


class Point2D(NamedTuple):
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __add__(self, other: Vector2D):
        if (type(other) is not Vector2D):
            raise TypeError("other must be Vector2D type.")
        return self.__class__(self.x + other.x, self.y + other.y)


class Maze:
    def __init__(self, floor_map_2d: list, start: Point2D,
                 goal: Point2D) -> None:
        self.floor = floor_map_2d
        self.start = start
        self.goal = goal

    def to_string(self) -> str:
        chars_2d = [[floor.to_char() for floor in row] for row in self.floor]
        lines = ["".join(row) for row in chars_2d]
        result = os.linesep.join(lines)
        return result

    @staticmethod
    def parse(s: str) -> Maze:
        Maze._validate(s)

        lines = s.splitlines()
        floors = [[EFloor.of(aChar) for aChar in line] for line in lines]

        start_at = Maze._find_xy(EFloor.Start, floors)
        goal_at = Maze._find_xy(EFloor.Goal, floors)
        return Maze(floors, start_at, goal_at)

    @staticmethod
    def _validate(s: str) -> None:
        has_start = EFloor.Start.to_char() in s
        if (not has_start):
            print("Error: Cannot find the beginning position. Abort program.")
            sys.exit(1)

        has_goal = EFloor.Goal.to_char() in s
        if (not has_goal):
            print("Error: Cannot find the exit position. Abort program.")
            sys.exit(1)

    @staticmethod
    def _find_xy(kind: EFloor, floor_map_2d: list) -> Point2D:
        x = [i for i, row in enumerate(floor_map_2d) if (kind in row)][0]
        y = floor_map_2d[x].index(kind)
        return Point2D(x, y)


class EOrientation(Enum):
    North = Vector2D(-1, 0)
    West = Vector2D(0, -1)
    South = Vector2D(+1, 0)
    East = Vector2D(0, +1)

    def turn_to_the_right(self) -> EOrientation:
        if self == EOrientation.North: return EOrientation.East
        if self == EOrientation.West: return EOrientation.North
        if self == EOrientation.South: return EOrientation.West
        if self == EOrientation.East: return EOrientation.South
        raise ValueError(f"{self} is not a valid {EOrientation.__name__}")

    def turn_to_the_left(self) -> EOrientation:
        if self == EOrientation.North: return EOrientation.West
        if self == EOrientation.West: return EOrientation.South
        if self == EOrientation.South: return EOrientation.East
        if self == EOrientation.East: return EOrientation.North
        raise ValueError(f"{self} is not a valid {EOrientation.__name__}")

    def turn_around(self) -> EOrientation:
        if self == EOrientation.North: return EOrientation.South
        if self == EOrientation.West: return EOrientation.East
        if self == EOrientation.South: return EOrientation.North
        if self == EOrientation.East: return EOrientation.West
        raise ValueError(f"{self} is not a valid {EOrientation.__name__}")

    def __str__(self) -> str:
        return f"{self.name.lower()}"


class Pose(NamedTuple):
    position: Point2D
    orientation: Vector2D


class Player:
    def __init__(self, position: Point2D, orientation: EOrientation) -> None:
        self.position = position
        self.orientation = orientation

    def is_located_at(self, pos: Point2D) -> bool:
        return self.position == pos

    def turn_to_the_right(self) -> None:
        self.orientation = self.orientation.turn_to_the_right()

    def keep_orientation(self) -> None:
        # do nothing intentionally
        return

    def turn_to_the_left(self) -> None:
        self.orientation = self.orientation.turn_to_the_left()

    def turn_around(self) -> None:
        self.orientation = self.orientation.turn_around()

    def step_forward(self) -> None:
        self.position = self.position + self.orientation.value

    def to_Pose(self) -> Pose:
        return Pose(self.position, self.orientation)


class MazeManager:
    def __init__(self, maze: Maze, player: Player) -> None:
        self.maze = maze
        self.player = player

    def process_players_trial(self) -> None:
        """Try to solve a given maze by using wall-follower algorithm.
        """
        print(f"Current position: {str(self.player.position)}")

        history = set()
        while (not (self.is_player_located_at_goal())
               and (self.player.to_Pose() not in history)):

            history.add(self.player.to_Pose())

            if (self.player_can_go_right()):
                self.player_turn_to_the_right()
                self.player_step_forward()
                continue

            elif (self.player_can_go_forward()):
                self.player_keep_orientation()
                self.player_step_forward()
                continue

            elif (self.player_can_go_left()):
                self.player_turn_to_the_left()
                self.player_step_forward()
                continue

            else:
                # go backward. no other choice.
                self.player_turn_around()
                self.player_step_forward()
                continue

        if self.is_player_located_at_goal():
            print(f"Exit at {str(self.player.position)}")
        else:
            print(f"There is no solution for this maze.")

    def is_player_located_at_goal(self) -> bool:
        return self.player.is_located_at(self.maze.goal)

    def player_can_go_right(self) -> bool:
        new_orientation = self.player.orientation.turn_to_the_right()
        next_pos = self.player.position + new_orientation.value
        return self._player_can_go(next_pos)

    def player_turn_to_the_right(self) -> None:
        self.player.turn_to_the_right()

    def _player_can_go(self, pos: Point2D) -> bool:
        return self.maze.floor[pos.x][pos.y] != EFloor.Wall

    def player_can_go_forward(self) -> bool:
        next_pos = self.player.position + self.player.orientation.value
        return self._player_can_go(next_pos)

    def player_keep_orientation(self) -> None:
        self.player.keep_orientation()

    def player_step_forward(self) -> None:
        print(f"At {str(self.player.position)}"
              f" facing {str(self.player.orientation)}")

        self.player.step_forward()

    def player_can_go_left(self) -> bool:
        new_orientation = self.player.orientation.turn_to_the_left()
        next_pos = self.player.position + new_orientation.value
        return self._player_can_go(next_pos)

    def player_turn_to_the_left(self) -> None:
        self.player.turn_to_the_left()

    def player_can_go_backward(self) -> bool:
        new_orientation = self.player.orientation.turn_around()
        next_pos = self.player.position + new_orientation.value
        return self._player_can_go(next_pos)

    def player_turn_around(self) -> None:
        self.player.turn_around()


if __name__ == "__main__":

    # This should be solved.
    maze1 = """\
*******
*o    *
* x****
*     *
*******"""

    # This should not be solved.
    maze2 = """\
*******
*     *
* *** *
*o*x* *
* *** *
*     *
*******"""

    # This should be solved, even though player initailly goes up.
    maze3 = """\
*****
** **
*   *
**o**
**x**
*****"""

    maze = Maze.parse(maze3)
    print(maze.to_string())

    manager = MazeManager(maze, Player(maze.start, EOrientation.North))
    manager.process_players_trial()
