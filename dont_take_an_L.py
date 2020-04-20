
import os
import time
import subprocess
import threading

from getkey import getkey

from classes import * # pylint: disable=unused-wildcard-import

FPS = 1/23

render_lock = threading.Lock()
control_lock = threading.Lock()

GAME_OVER = False
INPUT_CONTROL_EXIT = threading.Event()

def game_loop(space, player):
    threading.Thread(target=get_input, args=(player,)).start()
    while player.is_alive:
        # adjusted position is x pos - fire len to get distance from left most bound
        # offset, adjusted_pos, rocket = render_rocket(offset)
        player.forward()
        space.shift_debris()

        space.render(player)
        # giving player score per rendered frame/ page completion
        if (player.coordinates.x == space.max_width):
            player.adjust_score(50)
        else:
            player.adjust_score(1)

        time.sleep(FPS)

    player.explode()

def get_input(player):
    while player.is_alive or GAME_OVER:
        key = getkey(blocking=True)
        if key == 'w':
            player.control(DIR.UP)
        elif key == 's':
            player.control(DIR.DOWN)

    INPUT_CONTROL_EXIT.set()

#init
def initialize():
    global GAME_OVER
    # initializing space. POG
    space = Space(render_lock, control_lock)
    # generating first page of debri coords
    space.generate_debris()
    # initializing player and settings space bounds
    player = Rocket(space.dimensions, control_lock)

    try:
        game_loop(space, player)
    except KeyboardInterrupt:
        pass
    finally:
        GAME_OVER = True
        while not INPUT_CONTROL_EXIT:
            time.sleep(1)

if __name__ == '__main__':
    initialize()
