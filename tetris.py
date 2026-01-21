#!.venv/bin/python
import os

os.environ["TERM"] = "xterm-256color"
import re
import time
import json
import curses
import random
import datetime
from blessed import Terminal
from curses import wrapper


term = Terminal()
state = term.get_kitty_keyboard_state()
pressed = {}


def frames_to_ms(frames):
    return (frames * 1000) / 60


# default settings
handlings_default = {
    "das": 10,
    "arr": 2,
    "sdf": 6,
    "starting_level": 0,
    "width": 10,
    "height": 20,
}
controls_default = {
    "left": ["left", "4"],
    "right": ["right", "6"],
    "soft_drop": ["down", "2"],
    "hard_drop": [" ", "8"],
    "rotate_ccw": ["z", "3", "7"],
    "rotate_cw": ["up", "x", "1", "5", "9"],
    "rotate_180": ["a"],
    "hold": ["c", "0"],
}
path = __file__.replace(os.path.basename(__file__), "")

for attempt in range(0, 2):
    try:
        with open(f"{path}handling.json", "r") as file:
            handling = json.load(file)
    except FileNotFoundError:
        with open(f"{path}handling.json", "w") as file:
            file.write("""{
  "das":            10,
  "arr":            2,
  "sdf":            6,

  "starting_level": 0,

  "width":          10,
  "height":         20
}""")

for attempt in range(0, 2):
    try:
        with open(f"{path}controls.json", "r") as file:
            controls = json.load(file)
    except FileNotFoundError:
        with open(f"{path}controls.json", "w") as file:
            file.write("""{
  "left":       ["left", "4"],
  "right":      ["right", "6"],
  "soft_drop":  ["down", "2"],
  "hard_drop":  [" ", "8"],

  "rotate_ccw": ["z", "3", "7"],
  "rotate_cw":  ["up", "x", "1", "5", "9"],
  "rotate_180": ["a"],

  "hold":       ["c", "0"]
}
""")


handling = {**handlings_default, **handling}
controls = {**controls_default, **controls}
config = {**handling, **controls}
config["das"] = frames_to_ms(config["das"])
config["arr"] = frames_to_ms(config["arr"])

x_size, y_size = config["width"], config["height"]


levelspeed = [
    48,
    43,
    38,
    33,
    28,
    23,
    18,
    13,
    8,
    6,
    5,
    5,
    5,
    4,
    4,
    4,
    3,
    3,
    3,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    1,
]
for i in range(len(levelspeed)):
    levelspeed[i] = frames_to_ms(levelspeed[i])

minos = {
    # "0": "⌜⌟",
    "0": " .",
    "z": "[]",
    "l": "[]",
    "o": "[]",
    "s": "[]",
    "i": "[]",
    "j": "[]",
    "t": "[]",
}
mino_color = {
    "0": 1,
    "z": 2,
    "l": 3,
    "o": 4,
    "s": 5,
    "i": 6,
    "j": 7,
    "t": 8,
}

# board = [["0" for i in range(x_size)] for i in range(y_size)]
# board = [
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "l", "l", "0", "0", "0", "0", "0", "0"],
#     ["0", "0", "0", "l", "0", "0", "0", "0", "0", "0"],
#     ["t", "t", "0", "l", "0", "0", "0", "0", "0", "0"],
#     ["t", "0", "0", "i", "0", "0", "0", "0", "0", "0"],
#     ["z", "z", "0", "i", "l", "0", "0", "0", "0", "0"],
#     ["j", "z", "z", "i", "l", "0", "0", "z", "z", "0"],
#     ["j", "j", "j", "i", "l", "l", "0", "0", "z", "z"],
# ]


rotations = ["0", "R", "2", "L"]

pieces = {
    "z": {
        "0": [[0, 0], [-1, 1], [0, 1], [1, 0]],
        "R": [[0, 0], [1, 1], [1, 0], [0, -1]],
        "2": [[0, 0], [-1, 0], [0, -1], [1, -1]],
        "L": [[0, 0], [0, 1], [-1, 0], [-1, -1]],
    },
    "l": {
        "0": [[0, 0], [1, 1], [-1, 0], [1, 0]],
        "R": [[0, 0], [0, 1], [0, -1], [1, -1]],
        "2": [[0, 0], [-1, 0], [1, 0], [-1, -1]],
        "L": [[0, 0], [-1, 1], [0, 1], [0, -1]],
    },
    "o": {
        "0": [[0, 0], [0, 1], [1, 1], [1, 0]],
        "R": [[0, 0], [0, 1], [1, 1], [1, 0]],
        "2": [[0, 0], [0, 1], [1, 1], [1, 0]],
        "L": [[0, 0], [0, 1], [1, 1], [1, 0]],
    },
    "s": {
        "0": [[0, 0], [0, 1], [1, 1], [-1, 0]],
        "R": [[0, 0], [0, 1], [1, 0], [1, -1]],
        "2": [[0, 0], [1, 0], [-1, -1], [0, -1]],
        "L": [[0, 0], [-1, 1], [-1, 0], [0, -1]],
    },
    "i": {
        "0": [[0, 0], [-1, 0], [1, 0], [2, 0]],
        "R": [[1, 0], [1, 1], [1, -1], [1, -2]],
        "2": [[0, -1], [-1, -1], [1, -1], [2, -1]],
        "L": [[0, -1], [0, 1], [0, 0], [0, -2]],
    },
    "j": {
        "0": [[0, 0], [-1, 1], [-1, 0], [1, 0]],
        "R": [[0, 0], [0, 1], [1, 1], [0, -1]],
        "2": [[0, 0], [-1, 0], [1, 0], [1, -1]],
        "L": [[0, 0], [0, 1], [-1, -1], [0, -1]],
    },
    "t": {
        "0": [[0, 0], [0, 1], [-1, 0], [1, 0]],
        "R": [[0, 0], [0, 1], [1, 0], [0, -1]],
        "2": [[0, 0], [-1, 0], [1, 0], [0, -1]],
        "L": [[0, 0], [0, 1], [-1, 0], [0, -1]],
    },
}
for p in pieces:
    for i in pieces[p]:
        for b in pieces[p][i]:
            b[1] = b[1] * -1

kick_table = {
    "i": {
        "0 > L": [[0, 0], [-1, 0], [2, 0], [2, -1], [-2, 2]],
        "0 > R": [[0, 0], [1, 0], [-2, 0], [-2, -1], [2, 2]],
        "R > 0": [[0, 0], [-1, 0], [2, 0], [-1, -2], [2, 1]],
        "R > 2": [[0, 0], [-1, 0], [2, 0], [-1, 2], [2, -1]],
        "2 > R": [[0, 0], [-2, 0], [1, 0], [-2, 1], [1, -2]],
        "2 > L": [[0, 0], [2, 0], [-1, 0], [2, 1], [-1, -2]],
        "L > 2": [[0, 0], [1, 0], [-2, 0], [1, 2], [-2, -1]],
        "L > 0": [[0, 0], [1, 0], [-2, 0], [1, -2], [-2, 1]],
        # 180 rotations
        "0 > 2": [[0, 0], [0, 1], [1, 1], [-1, 1], [1, 0], [-1, 0]],
        "2 > 0": [[0, 0], [0, -1], [-1, -1], [1, -1], [-1, 0], [1, 0]],
        "R > L": [[0, 0], [1, 0], [1, 2], [1, 1], [0, 2], [0, 1]],
        "L > R": [[0, 0], [-1, 0], [-1, 2], [-1, 1], [0, 2], [0, 1]],
    },
    "zlosjt": {
        "0 > L": [[0, 0], [1, 0], [1, 1], [0, -2], [1, -2]],
        "0 > R": [[0, 0], [-1, 0], [-1, 1], [0, -2], [-1, -2]],
        "R > 0": [[0, 0], [1, 0], [1, -1], [0, 2], [1, 2]],
        "R > 2": [[0, 0], [1, 0], [1, -1], [0, 2], [1, 2]],
        "2 > R": [[0, 0], [-1, 0], [-1, 1], [0, -2], [-1, -2]],
        "2 > L": [[0, 0], [1, 0], [1, 1], [0, -2], [1, -2]],
        "L > 2": [[0, 0], [-1, 0], [-1, -1], [0, 2], [-1, 2]],
        "L > 0": [[0, 0], [-1, 0], [-1, -1], [0, 2], [-1, 2]],
        # 180 rotations
        "0 > 2": [[0, 0], [0, 1], [1, 1], [-1, 1], [1, 0], [-1, 0]],
        "2 > 0": [[0, 0], [0, -1], [-1, -1], [1, -1], [-1, 0], [1, 0]],
        "R > L": [[0, 0], [1, 0], [1, 2], [1, 1], [0, 2], [0, 1]],
        "L > R": [[0, 0], [-1, 0], [-1, 2], [-1, 1], [0, 2], [0, 1]],
    },
}
for p in kick_table:
    for i in kick_table[p]:
        for k in kick_table[p][i]:
            k[1] = k[1] * -1


def render_board():
    game_board.erase()
    game_board.border()

    """
    game_board.addstr(0, 0, f" {'▁' * (x_size * 2)} ")
    for i in range(y_size):
        game_board.addstr(i + 1, 0, f"▕{' ' * (x_size * 2)}▏")
    try:
        game_board.addstr(y_size + 1, 0, f" {'▔' * (x_size * 2)} ")
    except:
        pass
    """
    """
    game_board.addstr(0, 0, f"▄{'▄' * (x_size * 2)}▄")
    for i in range(y_size):
        game_board.addstr(i + 1, 0, f"█{' ' * (x_size * 2)}█")
    try:
        game_board.addstr(y_size + 1, 0, f"▀{'▀' * (x_size * 2)}▀")
    except:
        pass
    """
    for y in range(y_size):
        for x in range(x_size):
            game_board.addstr(
                y + 1,
                (x * 2) + 1,
                minos[board[y][x]],
                curses.color_pair(mino_color[board[y][x]]),
            )


def render_hold():
    hold_win.erase()
    hold_win.border()
    hold_win.addstr(0, 0, "    HOLD    ", curses.A_REVERSE)
    if piece.held:
        render_piece = piece.held

        offset_x = 0
        offset_y = 0
        if render_piece == "i" or render_piece == "o":
            if render_piece == "i":
                offset_y = -1
            offset_x = -1

        for i in range(len(pieces[render_piece]["0"])):
            x_offset = pieces[render_piece]["0"][i][0]
            y_offset = pieces[render_piece]["0"][i][1]

            if piece.can_hold:
                hold_win.addstr(
                    3 + y_offset + offset_y,
                    (2 * 2) + 1 + x_offset * 2 + offset_x,
                    minos[render_piece],
                    curses.color_pair(mino_color[render_piece]),
                )
            else:
                hold_win.addstr(
                    3 + y_offset + offset_y,
                    (2 * 2) + 1 + x_offset * 2 + offset_x,
                    minos[render_piece],
                    curses.color_pair(mino_color[render_piece] + 7),
                )
    hold_win.refresh()


def render_next():
    next_win.erase()
    next_win.border()
    next_win.addstr(0, 0, "    NEXT    ", curses.A_REVERSE)
    for next_piece in range(5):
        render_piece = piece.bag[next_piece]

        offset_x = 0
        offset_y = 0
        if render_piece == "i" or render_piece == "o":
            if render_piece == "i":
                offset_y = -1
            offset_x = -1

        for i in range(len(pieces[render_piece]["0"])):
            x_offset = pieces[render_piece]["0"][i][0]
            y_offset = pieces[render_piece]["0"][i][1]

            next_win.addstr(
                next_piece * 3 + 3 + y_offset + offset_y,
                (2 * 2) + 1 + x_offset * 2 + offset_x,
                minos[render_piece],
                curses.color_pair(mino_color[render_piece]),
            )
    next_win.refresh()


def render_score():
    score_win.erase()
    score_win.addstr(0, 0, "SCORE")
    score_win.addstr(1, 0, f"{piece.score:,}")
    score_win.refresh()


def format_time(seconds):
    td = datetime.timedelta(seconds=seconds)

    total_seconds = int(td.total_seconds())
    ms = int((seconds - total_seconds) * 1000) // 10

    h, rem = divmod(total_seconds, 3600)
    m, s = divmod(rem, 60)

    if h > 0:
        return f"{h}:{m:02}:{s:02}.{ms:02}"
    elif m > 0:
        return f"{m}:{s:02}.{ms:02}"
    else:
        return f"{s}.{ms:02}"


def render_stats():
    stats_win.erase()
    stats_win.addstr(0, 13 - len("LEVEL"), "LEVEL")
    stats_win.addstr(1, 13 - len(str(piece.level)), str(piece.level))
    stats_win.addstr(3, 13 - len("LINES"), "LINES")
    stats_win.addstr(4, 13 - len(str(piece.lines)), str(piece.lines))

    piece.time = format_time(time.time() - piece.time_start)

    stats_win.addstr(6, 13 - len("TIME"), "TIME")
    try:
        stats_win.addstr(7, 13 - len(str(piece.time)), str(piece.time))
    except:
        pass

    stats_win.refresh()


def key_priority(dict, a, b):
    if a not in dict:
        return False
    if b not in dict:
        return True

    keys = list(dict)
    return keys.index(a) > keys.index(b)


class Piece:
    def __init__(self):
        self.time_start = time.time()
        self.time = 0
        self.lines = 0
        self.level = min(
            config["starting_level"] + int(self.lines / 10), len(levelspeed) - 1
        )
        self.last_grav_time = time.time() * 1000
        bag = list(pieces.keys())
        random.shuffle(bag)
        self.bag = bag
        self.held = None
        self.score = 0
        self.can_hold = True
        self.dead = False

    def new_piece(self, hold=False):
        if hold:
            self.unrender()
            self.can_hold = False
        if hold and self.held:
            self.current, self.held = self.held, self.current

        if not hold or not self.held:
            if hold:
                self.held = self.current
            self.current = self.bag.pop(0)
            if len(self.bag) <= 7:
                bag = list(pieces.keys())
                random.shuffle(bag)
                self.bag += bag

        self.position = [round(x_size / 2) - 1, -1]
        self.rotation = "0"
        self.last_grav_time = time.time() * 1000
        self.been_on_ground = False
        self.lock_timer = 0
        self.lock_interrupt = 0

        if not hold:
            self.can_hold = True

        render_hold()
        render_next()
        self.render()

    def render(self):
        # render ghost piece
        is_valid = True
        indicator_y = self.position[1]
        for i in range(y_size):
            for block in pieces[self.current][self.rotation]:
                x_offset = block[0]
                y_offset = block[1]
                check = [
                    self.position[0] + block[0],
                    indicator_y + block[1] + 1,
                ]
                if check[0] < 0 or check[0] > x_size - 1:
                    is_valid = False
                    break
                if check[1] > y_size - 1:
                    is_valid = False
                    break
                if is_valid:
                    if check[1] >= 0:
                        if board[check[1]][check[0]] != "0":
                            is_valid = False
                            break
            if is_valid:
                indicator_y += 1

        for block in pieces[self.current][self.rotation]:
            x_offset = block[0]
            y_offset = block[1]
            if indicator_y + y_offset >= 0:
                game_board.addstr(
                    indicator_y + 1 + y_offset,
                    (self.position[0] * 2) + 1 + x_offset * 2,
                    minos[self.current],
                    curses.color_pair(mino_color[self.current] + 7),
                )

        # render actual piece
        for i in range(len(pieces[self.current][self.rotation])):
            x_offset = pieces[self.current][self.rotation][i][0]
            y_offset = pieces[self.current][self.rotation][i][1]

            block_y = self.position[1] + y_offset
            if block_y < 0 or block_y > y_size - 1:
                continue
            if self.position[1] + y_offset >= 0:
                game_board.addstr(
                    self.position[1] + 1 + y_offset,
                    (self.position[0] * 2) + 1 + x_offset * 2,
                    minos[self.current],
                    curses.color_pair(mino_color[self.current]),
                )

    def unrender(self):
        # render ghost piece
        is_valid = True
        indicator_y = self.position[1]
        for i in range(y_size):
            for block in pieces[self.current][self.rotation]:
                x_offset = block[0]
                y_offset = block[1]
                check = [
                    self.position[0] + block[0],
                    indicator_y + block[1] + 1,
                ]
                if check[0] < 0 or check[0] > x_size - 1:
                    is_valid = False
                    break
                if check[1] > y_size - 1:
                    is_valid = False
                    break
                if is_valid:
                    if check[1] >= 0:
                        if board[check[1]][check[0]] != "0":
                            is_valid = False
                            break
            if is_valid:
                indicator_y += 1

        for block in pieces[self.current][self.rotation]:
            x_offset = block[0]
            y_offset = block[1]
            if indicator_y + y_offset >= 0:
                game_board.addstr(
                    indicator_y + 1 + y_offset,
                    (self.position[0] * 2) + 1 + x_offset * 2,
                    minos["0"],
                    curses.color_pair(mino_color["0"]),
                )

        # render actual piece
        for i in range(len(pieces[self.current][self.rotation])):
            x_offset = pieces[self.current][self.rotation][i][0]
            y_offset = pieces[self.current][self.rotation][i][1]

            block_y = self.position[1] + y_offset
            if block_y < 0 or block_y > y_size - 1:
                continue
            if self.position[1] + y_offset >= 0:
                game_board.addstr(
                    self.position[1] + 1 + y_offset,
                    (self.position[0] * 2) + 1 + x_offset * 2,
                    minos["0"],
                    curses.color_pair(mino_color["0"]),
                )

    def move(self, x, y):
        is_valid = True
        for block in pieces[self.current][self.rotation]:
            check = [
                self.position[0] + block[0] + x,
                self.position[1] + block[1] + y,
            ]
            if check[0] < 0 or check[0] > x_size - 1:
                is_valid = False
                break
            if check[1] > y_size - 1:
                is_valid = False
                break
            if is_valid:
                if check[1] >= 0:
                    if board[check[1]][check[0]] != "0":
                        is_valid = False
        if is_valid:
            self.unrender()
            self.position[0] += x
            self.position[1] += y
            self.render()
            if piece.been_on_ground:
                if piece.on_ground():
                    if piece.lock_interrupt < 15:
                        piece.lock_timer = time.time()
                        piece.lock_interrupt += 1
        return is_valid

    def on_ground(self):
        is_valid = True
        for block in pieces[self.current][self.rotation]:
            check = [
                self.position[0] + block[0],
                self.position[1] + block[1] + 1,
            ]
            if check[0] < 0 or check[0] > x_size - 1:
                is_valid = False
                break
            if check[1] > y_size - 1:
                is_valid = False
                break
            if is_valid:
                if check[1] >= 0:
                    if board[check[1]][check[0]] != "0":
                        is_valid = False
        return not is_valid

    def rotate(self, direction):
        if self.current == "i":
            kick_piece = "i"
        else:
            kick_piece = "zlosjt"
        new_rotation = rotations[(rotations.index(self.rotation) + direction) % 4]
        for kick in kick_table[kick_piece][f"{self.rotation} > {new_rotation}"]:
            is_valid = True
            for block in pieces[self.current][new_rotation]:
                if not is_valid:
                    continue
                check = [
                    self.position[0] + block[0] + kick[0],
                    self.position[1] + block[1] + kick[1],
                ]
                if check[0] < 0 or check[0] > x_size - 1:
                    is_valid = False
                    break
                if check[1] > y_size - 1:
                    is_valid = False
                    break
                if is_valid:
                    if check[1] >= 0:
                        if board[check[1]][check[0]] != "0":
                            is_valid = False
            if is_valid:
                self.unrender()
                self.position = [
                    self.position[0] + kick[0],
                    self.position[1] + kick[1],
                ]
                self.rotation = new_rotation
                self.render()
                if piece.been_on_ground:
                    if piece.on_ground():
                        if piece.lock_interrupt < 15:
                            piece.lock_timer = time.time()
                            piece.lock_interrupt += 1
                return True
        return False

    def gravity(self, sdf):
        current_time = time.time() * 1000
        if sdf <= 0:
            while self.move(0, 1):
                self.score += 1
            render_score()
            return
        if sdf < 5:
            sdf = 1
        if current_time - self.last_grav_time > levelspeed[self.level] / sdf:
            if not self.on_ground():
                if sdf > 1:
                    self.score += 1
                    render_score()
                self.move(0, 1)
            self.last_grav_time = time.time() * 1000

    def lock(self):
        for block in pieces[self.current][self.rotation]:
            check = [(self.position[0] + block[0]), (self.position[1] + block[1])]
            if check[1] < 0:
                self.dead = True
                continue
            board[check[1]][check[0]] = self.current

        rows_cleared = 0
        for y in range(len(board)):
            if "0" not in board[y]:
                board.pop(y)
                board.insert(0, ["0"] * x_size)
                rows_cleared += 1
                self.lines += 1

        if rows_cleared == 1:
            self.score += 100 * (self.level + 1)
        elif rows_cleared == 2:
            self.score += 300 * (self.level + 1)
        elif rows_cleared == 3:
            self.score += 500 * (self.level + 1)
        elif rows_cleared == 4:
            self.score += 800 * (self.level + 1)

        self.level = min(
            config["starting_level"] + int(self.lines / 10), len(levelspeed) - 1
        )

        if rows_cleared > 0:
            render_board()
        render_score()
        self.new_piece()


def main(stdscr):
    global piece
    global game_board
    global hold_win
    global next_win
    global score_win
    global stats_win
    global board
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    # mocha colors
    # 313244
    curses.init_color(16, 49 * 1000 // 255, 50 * 1000 // 255, 68 * 1000 // 255)
    # f38ba8
    curses.init_color(17, 243 * 1000 // 255, 139 * 1000 // 255, 168 * 1000 // 255)
    # fab387
    curses.init_color(18, 250 * 1000 // 255, 179 * 1000 // 255, 135 * 1000 // 255)
    # f9e2af
    curses.init_color(19, 249 * 1000 // 255, 226 * 1000 // 255, 175 * 1000 // 255)
    # a6e3a1
    curses.init_color(20, 166 * 1000 // 255, 227 * 1000 // 255, 161 * 1000 // 255)
    # 89dceb
    curses.init_color(21, 137 * 1000 // 255, 220 * 1000 // 255, 235 * 1000 // 255)
    # 89b4fa
    curses.init_color(22, 137 * 1000 // 255, 180 * 1000 // 255, 250 * 1000 // 255)
    # cba6f7
    curses.init_color(23, 203 * 1000 // 255, 166 * 1000 // 255, 247 * 1000 // 255)

    # latte colors
    curses.init_color(24, 49 * 1000 // 255, 50 * 1000 // 255, 68 * 1000 // 255)

    curses.init_color(25, 210 * 1000 // 255, 15 * 1000 // 255, 57 * 1000 // 255)
    curses.init_color(26, 254 * 1000 // 255, 100 * 1000 // 255, 11 * 1000 // 255)
    curses.init_color(27, 223 * 1000 // 255, 142 * 1000 // 255, 29 * 1000 // 255)
    curses.init_color(28, 64 * 1000 // 255, 160 * 1000 // 255, 43 * 1000 // 255)
    curses.init_color(29, 4 * 1000 // 255, 165 * 1000 // 255, 229 * 1000 // 255)
    curses.init_color(30, 32 * 1000 // 255, 102 * 1000 // 255, 245 * 1000 // 255)
    curses.init_color(31, 136 * 1000 // 255, 57 * 1000 // 255, 239 * 1000 // 255)

    curses.init_pair(1, 16, -1)  # #313244 as fg
    curses.init_pair(2, 25, 17)  # #f38ba8 as bg
    curses.init_pair(3, 26, 18)  # #fab387 as bg
    curses.init_pair(4, 27, 19)  # #f9e2af as bg
    curses.init_pair(5, 28, 20)  # #a6e3a1 as bg
    curses.init_pair(6, 29, 21)  # #89dceb as bg
    curses.init_pair(7, 30, 22)  # #89b4fa as bg
    curses.init_pair(8, 31, 23)  # #cba6f7 as bg

    # mocha colors as fg
    curses.init_pair(9, 17, -1)
    curses.init_pair(10, 18, -1)
    curses.init_pair(11, 19, -1)
    curses.init_pair(12, 20, -1)
    curses.init_pair(13, 21, -1)
    curses.init_pair(14, 22, -1)
    curses.init_pair(15, 23, -1)

    board = [["0" for i in range(x_size)] for i in range(y_size)]

    while True:
        try:
            stdscr.clear()
            stdscr.refresh()
            height, width = stdscr.getmaxyx()
            game_board = curses.newwin(
                y_size + 2,
                (x_size * 2) + 2,
                (height - y_size - 2) // 2,
                (width - (x_size * 2) - 2) // 2,
            )

            hold_win = curses.newwin(
                6,
                12,
                (height - y_size - 2) // 2,
                (width - (x_size * 2) - 2) // 2 - 12,
            )

            next_win = curses.newwin(
                18,
                (4 * 2) + 4,
                (height - y_size - 2) // 2,
                (width - (x_size * 2) - 2) // 2 + (x_size * 2 + 2),
            )

            score_win = curses.newwin(
                2,
                13,
                (height - y_size - 2) // 2 + 16 + 2,
                (width - (x_size * 2) - 2) // 2 + (x_size * 2 + 2),
            )

            stats_win = curses.newwin(
                8,
                13,
                max(
                    (height - y_size - 2) // 2 + 6,
                    (height - y_size - 2) // 2 + y_size + 2 - 8,
                ),
                (width - (x_size * 2) - 2) // 2 - 12 - 1,
            )
            break
        except:
            pass

    # game_board.border()
    # game_board.refresh()
    # hold_win.border()
    # hold_win.refresh()
    # next_win.border()
    # next_win.refresh()

    # score_win.refresh()

    # stats_win.border()
    # stats_win.refresh()

    piece = Piece()
    render_board()
    render_hold()
    render_next()
    render_stats()

    render_score()
    piece.new_piece()

    game_board.refresh()

    with term.enable_kitty_keyboard(report_events=True):
        with term.cbreak():
            while not piece.dead:
                key = term.inkey(timeout=0)
                try:
                    seq = str(key)
                    match = re.search(r"\x1b\[(\d+)", seq)
                    identifier = key.value or (
                        chr(int(match.group(1))) if match else str(key)[0]
                    )
                except:
                    identifier = key.value or str(key) or None
                try:
                    if "KEY_" in key.name:
                        identifier = (
                            key.name.replace("KEY_", "")
                            .replace("KP_", "")
                            .replace("_RELEASED", "")
                            .lower()
                        )
                except:
                    pass

                if identifier == "q":
                    exit(0)
                    break

                kb = next(
                    (
                        k
                        for k, v in config.items()
                        if (v == identifier)
                        or (isinstance(v, list) and identifier in v)
                    ),
                    None,
                )
                if key.pressed:
                    if kb:
                        if kb not in pressed:
                            pressed[kb] = [
                                time.time() * 1000,
                                True,
                                time.time() * 1000,
                            ]  # [initial_press_time, is_initial_press, last_arr_move]

                elif key.released:
                    try:
                        del pressed[kb]
                    except KeyError:
                        pass

                current_time = time.time() * 1000

                # LEFT PRESSED
                if "left" in pressed:
                    k = "left"
                    if key_priority(pressed, k, "right"):
                        if pressed[k][1]:
                            piece.move(-1, 0)
                        elif current_time - pressed[k][0] > config["das"]:
                            if current_time - pressed[k][2] > config["arr"]:
                                piece.move(-1, 0)
                                pressed[k][2] = time.time() * 1000

                # RIGHT PRESSED
                if "right" in pressed:
                    k = "right"
                    if key_priority(pressed, k, "left"):
                        if pressed[k][1]:
                            piece.move(1, 0)
                        elif current_time - pressed[k][0] > config["das"]:
                            if current_time - pressed[k][2] > config["arr"]:
                                piece.move(1, 0)
                                pressed[k][2] = time.time() * 1000

                # HARD DROP PRESSED
                if "hard_drop" in pressed:
                    k = "hard_drop"
                    if pressed[k][1]:
                        while piece.move(0, 1):
                            piece.score += 2
                        piece.lock()

                # SOFT DROP PRESSED
                if "soft_drop" in pressed:
                    sdf = config["sdf"]
                else:
                    sdf = 1

                # ROTATE CCW PRESSED
                if "rotate_ccw" in pressed:
                    k = "rotate_ccw"
                    if pressed[k][1]:
                        piece.rotate(-1)

                # ROTATE CW PRESSED
                if "rotate_cw" in pressed:
                    k = "rotate_cw"
                    if pressed[k][1]:
                        piece.rotate(1)

                # ROTATE 180 PRESSED
                if "rotate_180" in pressed:
                    k = "rotate_180"
                    if pressed[k][1]:
                        piece.rotate(2)

                # HOLD PRESSED
                if "hold" in pressed:
                    k = "hold"
                    if pressed[k][1]:
                        if piece.can_hold:
                            piece.new_piece(hold=True)

                piece.gravity(sdf)
                if not piece.been_on_ground:
                    if piece.on_ground():
                        piece.been_on_ground = True
                        piece.lock_timer = time.time()
                else:
                    if piece.on_ground():
                        if time.time() - piece.lock_timer >= 0.5:
                            piece.lock()

                game_board.refresh()

                render_stats()

                if state is None:
                    try:
                        del pressed[kb]
                    except KeyError:
                        pass
                else:
                    if key.pressed:
                        if kb:
                            pressed[kb][1] = False

                new_height, new_width = stdscr.getmaxyx()
                if height != new_height or width != new_width:
                    while True:
                        try:
                            height, width = stdscr.getmaxyx()
                            stdscr.clear()
                            stdscr.refresh()

                            game_board.resize(y_size + 2, (x_size * 2) + 2)
                            game_board.mvwin(
                                (height - y_size - 2) // 2,
                                (width - (x_size * 2) - 2) // 2,
                            )

                            next_win.resize(18, 12)  # Adjust as needed
                            next_win.mvwin(
                                (height - y_size - 2) // 2,
                                (width - (x_size * 2) - 2) // 2 + (x_size * 2 + 2),
                            )

                            hold_win.resize(6, 12)  # 4+2=6 height, (4*2)+4=12 width
                            hold_win.mvwin(
                                (height - y_size - 2) // 2,
                                (width - (x_size * 2) - 2) // 2 - 12,
                            )

                            score_win.resize(2, 13)
                            score_win.mvwin(
                                (height - y_size - 2) // 2 + 16 + 2,
                                (width - (x_size * 2) - 2) // 2 + (x_size * 2 + 2),
                            )

                            stats_win.resize(8, 13)
                            stats_win.mvwin(
                                max(
                                    (height - y_size - 2) // 2 + 6,
                                    (height - y_size - 2) // 2 + y_size + 2 - 8,
                                ),
                                (width - (x_size * 2) - 2) // 2 - 12 - 1,
                            )

                            # hold_win.clear()
                            # hold_win.border()

                            # game_board.clear()
                            # game_board.border()

                            # next_win.clear()
                            # next_win.border()

                            render_board()
                            render_hold()
                            render_next()

                            render_score()

                            piece.render()
                            break
                        except:
                            pass


while True:
    wrapper(main)
