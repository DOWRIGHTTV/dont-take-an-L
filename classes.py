#!/usr/bin/env/python3

import math
import subprocess

from time import sleep
from random import randint

from enum import Enum
from collections import namedtuple

DEBUG = False


__all__ = (
    'Space', 'Rocket', 'COORDS', 'DEBRIS', 'DIR'
)

COORDS = namedtuple('coordinates', 'x y')
DEBRIS  = namedtuple('debris', 'type shield damage coords')

FPS = 1/16
DEV_SHIELD_EXTRAVAGANZA = True

class DIR(Enum):
    UP = 'w'
    DOWN = 's'


class UPGRADES(Enum):
    S_SHIELD = 's'
    L_SHIELD = 'S'
    EXTRA_LIFE = ''


class Cl:
    PINK = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'

    ENDC = '\033[0m'


class Space:
    def __init__(self, render_lock, control_lock):
        self._render_lock  = render_lock
        self._control_lock = control_lock

        self.max_width  = 160
        self.min_height = 1
        self.max_height = 25

        self._right_bound = int(self.max_width)

        self.dimensions = (self.max_width, self.max_height)

        self.debris_count = 19
        self.debris_locations = {}

        self._pad_debug = 0

        # NOTE: should be offsetting for a debri or if shield present
        self.max_width -= 3

        self._debris_condition = tuple([self.max_width/i for i in range(1,9)])

    def render(self, player):
        self._player = player

        # distance from left | rocket | *if debris, distance from rocket
        with self._render_lock:
            self._draw_top(player)
            # debris will be rendered off screen 2 times per page.
            if (player.coordinates.x in self._debris_condition):
                self.generate_debris()

            with self._control_lock:
                for y_coord in range(self.max_height, -1, -1):
                    self._y_coord, self._right_bound, self._line = y_coord, int(self.max_width), []
                    if player.coordinates.y == y_coord:
                        self._line.append(str(self._player))

                        self._right_bound = player.coordinates.x

                        self._pad_debug = self.max_width - self._right_bound

                    self._handle_debris()
                    self._draw_line()

                self._draw_bottom()

    def generate_debris(self):
        for _ in range(self.debris_count):
            for _ in range(2):
                rand_x = randint(self.max_width, self.max_width*2)
                rand_y = randint(2, self.max_height-2)
                if rand_y not in self.debris_locations:
                    dtype = randint(0,1000)
                    if (565 <= dtype < 570):
                        debris_data = DEBRIS('S', 50, 0, [rand_x, -1])

                    elif (550 <= dtype < 600):
                        debris_data = DEBRIS('s', 25, 0, [rand_x, -1])

                    elif (250 <= dtype < 550 or 600 <= dtype < 900):
                        debris_data = DEBRIS('l', 0, 50, [rand_x, -1])

                    else:
                        debris_data = DEBRIS('L', 0, 100, [rand_x, -1])

                    self.debris_locations[rand_y] = debris_data
                    break

    def shift_debris(self):
        locations_copy = list(self.debris_locations.items())
        for y_coord, debris in locations_copy:
            if debris.coords[0] > 0:
                self.debris_locations[y_coord].coords[0] -= 1
            else:
                self.debris_locations.pop(y_coord)

    def _handle_debris(self):
        # shield = True
        # checking for presence of debris, then making adjustments based on player position
        debris = self.debris_locations.get(self._y_coord, None)
        if debris is not None and debris.coords[0] < self.max_width:
            if (self._line): # player is sharing a line with a debris
                debris_dif = debris.coords[0] - self._player.coordinates.x
                # if not self._player.is_shielded:
                #     shield = False
                if (debris_dif in range(-4, 1)): # player hit debris :(
                    if debris.type in ['s', 'S']:
                        self._player.add_shield(debris)
                        # if (not shield):
                        #     self._right_bound += 6 # coloring code adjustment.
                    else:
                        self._player.damage(debris.damage)
                    # removing debris from space
                    self.debris_locations.pop(self._y_coord)

                # player heading towards debris
                elif (debris_dif > 0):
                    distance_to_player = debris.coords[0] - self._player.coordinates.x

                    self._right_bound = debris.coords[0]
                    if (self._player.has_moved):
                        self._right_bound += 1
                        distance_to_player -= 1
                    # if (self._player.is_shielded):
                    #     self._right_bound += 10
                    #     distance_to_player += 10

                    self._line.append(f"{' '*distance_to_player}{debris.type}")

                # player heading away from debris
                elif (debris_dif < -4):
                    back_of_player = self._player.coordinates.x - len(self._player)
                    distance_to_player = back_of_player - debris.coords[0]

                    self._line.insert(0, f"{debris.type}{' '*distance_to_player}")

                    self._right_bound = self._player.coordinates.x

            else:
                self._line.append(f"{' '*debris.coords[0]}{debris.type}")
                if (self._player.has_moved):
                    self._right_bound -= 2

                self._right_bound = debris.coords[0]

    def _draw_line(self):
        # if DEBUG:
        #     if self.max_width - self._right_bound > 0:
        #         self._line.insert(0, f'{self.max_width - self._right_bound}')
        self._line.append(f' '*((self.max_width) - self._right_bound))
        line = ''.join(self._line).rjust(self.max_width, ' ')
        print(line, end='\r')
        # sliding down cursor to new line
        print('')

    def _draw_top(self, player):
        subprocess.run('clear', shell=True)
        print(f'p1| score={player.score} hp={player.health} shield={player.shield} lives={player.lives} x={player.coordinates.x} y={player.coordinates.y}')
        print('='*self.max_width)

    def _draw_bottom(self):
        print('='*self.max_width)
#        print(self.debris_locations)

# yellow ,green, yellow/green, blue
# ')', ')', '|)', ,'))'
class Rocket:
    texture = '+==>'
    # shield_textures = {
    #     0: '',
    #     25: Cl.YELLOW + ')' + Cl.ENDC,
    #     50: Cl.GREEN + ')' + Cl.ENDC,
    #     75: Cl.YELLOW + '|' + Cl.ENDC + Cl.GREEN + ')' + Cl.ENDC,
    #     100: Cl.BLUE + '))' + Cl.ENDC
    # }
    shield_textures = {
        0: '',
        25: ')',
        50: ')',
        75: '|)',
        100: '))'
    }

    MAX_FIRE_LEN = 3
    DEFAULT_HEALTH = 100
    def __init__(self, space_dimensions, control_lock):
        self._x_position = 0 # nose of rocket
        self._y_position = 6 # height of rocket

        self._last_y_pos = int(self._y_position)

        self._total_len = 0

        self.max_width, self.max_height = space_dimensions
        self._control_lock = control_lock

        self.score  = 0
        self.lives  = 1
        self.health = self.DEFAULT_HEALTH
        self.shield = 25

        self._exhaust = 0

    def __len__(self):
        return self._total_len

    def __str__(self):
        # NOTE: maybe space class should control when the rocket position resets???
        if (self._x_position == self.max_width):
            self._x_position = 0

        # bad transition on wrap around
        if self._x_position == 0:
            self._total_len = 0
            return ''

        if self._x_position + len(self.texture) <= 10:
            rocket = self.texture
            rocket = rocket[-self._x_position:]
        else:
            rocket = self.exhaust + self.texture

        self._total_len = len(rocket)

        return rocket + self.shield_textures[self.shield]

    def adjust_score(self, amt):
        self.score += amt

    def forward(self):
        with self._control_lock:
            self._x_position += 1
            # updating y pos for movement detection
            self._last_y_pos = int(self._y_position)

    def control(self, d):
        with self._control_lock:
            # updating last position for movement detection
            self._last_y_pos = int(self._y_position)
            if (d is DIR.UP and self._y_position < self.max_height):
                self._y_position += 1

            elif (d is DIR.DOWN and self._y_position > 0):
                self._y_position -= 1

    def add_shield(self, upgrade):
        up_type = UPGRADES(upgrade.type)
        if (up_type == UPGRADES.S_SHIELD):
            self.shield += 25

        elif (up_type == UPGRADES.L_SHIELD):
            self.shield += 50

        if (self.shield > 100):
            self.shield = 100

        for i, val in enumerate([25, 75]):
            if self.shield == val:
                self._x_position += i

    def damage(self, amount):
        if (self.is_shielded):
            self.shield -= amount
            if (self.shield < 0):
                amount = int(math.fabs(-amount))
                self.shield = 0

        self.health -= amount
        if not self.is_alive and self.lives:
            self.lives -= 1
            self.health = self.DEFAULT_HEALTH

    def explode(self):
        y_pos_one = int(self._y_position)
        y_pos_two = int(self._y_position)

        x_pos = int(self._x_position)
        for i in range(20):
            subprocess.run('clear', shell=True)
            for y_pos in range(self.max_height, 0, -1):
                if not i:
                    boom = '*'
                else:
                    boom = '*' + ' '*(i-1) + '*'

                if (y_pos == y_pos_one+1):
                    boom = '*' + ' '*(i-1) + '*'
                    print(f"{x_pos*' '}{boom}", end='\r')
                if y_pos in [y_pos_one, y_pos_two]:
                    print(f"{x_pos*' '}{boom}", end='\r')
                print('')

            x_pos -= 1
            y_pos_one += 1
            y_pos_two -= 1
            sleep(FPS*2)

    # NOTE: color exhausty stuff, no worky good :(
    # def _create_exhaust(self, exhaust=None):
    #     if (not exhaust):
    #         exhaust = self.exhaust

    #     return Cl.RED + exhaust + Cl.ENDC

    @property
    def has_moved(self):
        return self._last_y_pos != self._y_position

    @property
    def coordinates(self):
        return COORDS(self._x_position, self._y_position)

    @property
    def exhaust(self):
        if (self._exhaust < self.MAX_FIRE_LEN):
            self._exhaust += 1
        else:
            self._exhaust -= 1

        return '-'*self._exhaust

    @property
    def is_shielded(self):
        return self.shield > 0

    @property
    def is_alive(self):
        return self.health > 0
