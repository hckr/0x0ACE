#!/usr/bin/env python3

from telnetlib import Telnet
from PIL import Image
import numpy as np
import time
import sys
import atexit


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
        return tuple((pos_x, pos_y) + self.DIRECTIONS[self.direction])


class Maze:
    UNKNOWN = 4
    VISITED = 3
    CLEAR = 2
    WALL = 1

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.pos_x = width // 2
        self.pos_y = height // 2
        self.points = np.ones((width, height)) * self.UNKNOWN
        self.times_visited = np.zeros((width, height))
        self.direction = Direction()
        self.prev_cmd = None

    def update(self, pos_x, pos_y, value):
        self.points[pos_x, pos_y] = value
        if value == self.VISITED:
            self.times_visited[pos_x, pos_y] += 1

    def next_step_forward(self):
        return self.direction.step(self.pos_x, self.pos_y)

    def set_wall_at_front(self):
        wall_x, wall_y = self.next_step_forward()
        self.update(wall_x, wall_y, self.WALL)

    def set_clear_at_front(self):
        clear_x, clear_y = self.next_step_forward()
        self.update(clear_x, clear_y, self.CLEAR)

    def get_field_at_front(self):
        new_pos = self.next_step_forward()
        return self.points[new_pos]

    def is_within_range(self, pos_x, pos_y):
        return pos_x >= 0 and pos_y >= 0 and \
               pos_x < self.width and pos_y < self.height

    def can_step_forward(self, new_pos=None):
        if new_pos is None:
            new_pos = self.next_step_forward()
        if not self.is_within_range(*new_pos):
            return False
        if self.points[new_pos] == self.WALL:
            return False
        if self.points[new_pos] == self.CLEAR:
            return True
        if self.points[new_pos] == self.VISITED:
            return True
        return None

    def least_visited_adjacent_point_command(self):
        commands = {} # { command: resulting point times visited }

        new_dir = Direction(self.direction.direction)

        new_pos = new_dir.step(self.pos_x, self.pos_y)
        csf = self.can_step_forward()
        if self.is_within_range(*new_pos) and csf != False:
            commands[(csf, 'step')] = self.times_visited[new_pos]

        if self.prev_cmd != 'turn right':
            new_dir.turn_left()
            new_pos = new_dir.step(self.pos_x, self.pos_y)
            csf = self.can_step_forward(new_pos)
            if self.is_within_range(*new_pos) and self.points[new_pos] != self.WALL:
                commands[(csf, 'turn left')] = self.times_visited[new_pos]

        if self.prev_cmd != 'turn left':
            new_dir = Direction(self.direction.direction)

            new_dir.turn_right()
            new_pos = new_dir.step(self.pos_x, self.pos_y)
            csf = self.can_step_forward(new_pos)
            if self.is_within_range(*new_pos) and self.points[new_pos] != self.WALL:
                commands[(csf, 'turn right')] = self.times_visited[new_pos]

            new_dir.turn_right()
            new_pos = new_dir.step(self.pos_x, self.pos_y)
            csf = self.can_step_forward(new_pos)
            if self.is_within_range(*new_pos) and self.points[new_pos] != self.WALL:
                commands[(csf, 'turn right')] = min(commands.get('turn right', 0),
                                                    self.times_visited[new_pos])

        if len(commands) == 0:
            return None

        best_cmd = min(commands, key=commands.get)
        print(best_cmd)
        if best_cmd[1] != 'step' or best_cmd[0] == True:
            return best_cmd[1]
        return 'look'

    def command(self, cmd):
        self.prev_cmd = cmd
        if cmd == 'step':
            new_pos = self.next_step_forward()
            if not self.is_within_range(*new_pos):
                raise Exception('out of bounds')
            self.pos_x, self.pos_y = new_pos
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
    try:
        execute_command.counter += 1
    except AttributeError:
        execute_command.counter = 1
    print('%09d: %s' % (execute_command.counter, cmd))
    tn.write(str.encode(cmd))
    res = u''
    attempts = 0
    while len(res) == 0:
        attempts += 1
        if attempts > 50:
            print('No response, disconnecting.')
            sys.exit(1)
        time.sleep(0.1)
        res = tn.read_some()
    print(res)
    maze.command(cmd)
    if cmd == 'look':
        if res == b'wall':
            maze.set_wall_at_front()
        else:
            maze.set_clear_at_front()
    return res


def main():
    key = b'OoD5w68x52PGDWQenq60x4da1zZpjL7g2yXgylKbwNV9o8rAJmYROvEMkeP1aRqY'
    maze = Maze(50, 50)
    turning_chance = 0.05

    atexit.register(lambda: (print('Exited at', time.strftime('%H:%M:%S')), maze.save_image('maze.gif', 10)))

    # using IPv6 proxy (socat) to [2a01:4f8:160:5263::e3d3:467f]:2766
    with Telnet('212.237.30.120', 2766) as tn:
        res = tn.read_until(b'show me your key.')
        print(res)
        tn.write(key)
        res = tn.read_until(b'0x0ACE')
        print(res)
        if res == b"you can't start over again that quick. please wait":
            sys.exit(1)

        def cmd(command):
            res = execute_command(tn, maze, command)
            if execute_command.counter % 10 == 0:
                maze.save_image('maze.gif', 10)
            return res

        while True:
            can_step_forward = maze.can_step_forward()
            # if can_step_forward == None:
            #     res = cmd('look')
            #     if res == b'wall':
            #         can_step_forward = False
            #     else:
            #         can_step_forward = True
            #
            # if can_step_forward == True and maze.get_field_at_front() != Maze.VISITED:
            #     cmd('step')
            #     continue
            #
            prop_cmd = maze.least_visited_adjacent_point_command()
            if np.random.random() < 0.8 and prop_cmd != None:
                cmd(prop_cmd)
            elif can_step_forward == False:
                if np.random.random() < 0.5:
                    cmd('turn right')
                else:
                    cmd('turn left')
            elif can_step_forward == None:
                cmd('look')
            else:
                cmd('step')


if __name__ == '__main__':
    main()
