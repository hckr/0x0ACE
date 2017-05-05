#!/usr/bin/env python3

from telnetlib import Telnet
from PIL import Image
import numpy as np
import time
import sys


class Direction:
    UP = 0
    RIGHT = 1
    BOTTOM = 2
    LEFT = 3
    # (diff_x, diff_y)
    DIRECTIONS = np.array(((0, 1), (1, 0), (0, -1), (-1, 0)))
    DIRECTIONS_COUNT = len(DIRECTIONS)

    def __init__(self, initial=UP):
        self.direction = initial

    def cycle(self, shift):
        return (self.direction + shift) % self.DIRECTIONS_COUNT

    def turn_right(self):
        self.direction = self.cycle(1)

    def turn_left(self):
        self.direction = self.cycle(-1)

    def step(self, pos_x, pos_y):
        return (pos_x, pos_y) + self.DIRECTIONS[self.direction]


class Maze:
    UNKNOWN = 4
    VISITED = 3
    WALL = 1

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.pos_x = width // 2
        self.pos_y = height // 2
        self.points = np.ones((width, height)) * self.UNKNOWN
        self.direction = Direction()

    def update(self, pos_x, pos_y, value):
        self.points[pos_x, pos_y] = value

    def set_wall_at_front(self):
        wall_x, wall_y = self.direction.step(self.pos_x, self.pos_y)
        self.update(wall_x, wall_y, self.WALL)

    def can_step_forward(self):
        result_x, result_y = self.direction.step(self.pos_x, self.pos_y)
        if result_x < 0 or result_y < 0 or \
           result_x >= self.width or result_y >= self.height:
                return False
        if self.points[result_x, result_y] == self.WALL:
            return False
        if self.points[result_x, result_y] == self.VISITED:
            return True
        return None

    def command(self, cmd):
        if cmd == 'step':
            self.pos_x, self.pos_y = self.direction.step(self.pos_x, self.pos_y)
            if self.pos_x < 0 or self.pos_y < 0 or \
               self.pos_x >= self.width or self.pos_y >= self.height:
                    raise Exception('out of bounds')
            self.update(self.pos_x, self.pos_y, self.VISITED)
        elif cmd == 'turn right':
            self.direction.turn_right()
        elif cmd == 'turn left':
            self.direction.turn_left()

    def save_image(self, file_name, zoom=1):
        grayscale = self.points * 63
        grayscale[self.pos_x, self.pos_y] = 0
        Image.fromarray(np.rot90(grayscale).astype(np.uint8)).resize((self.width * zoom, self.height * zoom)).save(file_name)


def execute_command(tn, maze, cmd):
    print(cmd, file=sys.stderr)
    tn.write(str.encode(cmd))
    res = u''
    while len(res) == 0:
        time.sleep(0.1)
        res = tn.read_some()
    print(res)
    maze.command(cmd)
    if cmd == 'look' and res == b'wall':
        maze.set_wall_at_front()
    return res


def main():
    key = b'OoD5w68x52PGDWQenq60x4da1zZpjL7g2yXgylKbwNV9o8rAJmYROvEMkeP1aRqY'
    maze = Maze(200, 200)
    # using IPv6 proxy (socat) to [2a01:4f8:160:5263::e3d3:467f]:2766
    with Telnet('212.237.30.120', 2766) as tn:
        res = tn.read_until(b'show me your key.')
        print(res)
        tn.write(key)
        res = tn.read_until(b'0x0ACE')
        print(res)
        if res == b"you can't start over again that quick. please wait":
            sys.exit(1)
        i = 0
        while True:
            can_step_forward = maze.can_step_forward()
            if can_step_forward == None:
                res = execute_command(tn, maze, 'look')
                if res == b'wall':
                    can_step_forward = False
                else:
                    can_step_forward = True
            if res != b'exit' and (can_step_forward == False or np.random.random() < 0.2):
                if np.random.random() < 0.5:
                    execute_command(tn, maze, 'turn right')
                else:
                    execute_command(tn, maze, 'turn left')
            else:
                execute_command(tn, maze, 'step')
            if i % 100 == 0:
                maze.save_image('maze.png', 5)
            i += 1


if __name__ == '__main__':
    main()
