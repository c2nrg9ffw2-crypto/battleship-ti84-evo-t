# Battleship for the TI-84 Evo
# Sink all 5 of the other side's ships before they sink yours.
# A hit means you fire again; a miss ends your turn.
# 1 player: against the calculator. 2 players: pass the calculator;
# a black screen in between shows whose turn it is.
# Keys: arrows = aim / move a ship, 2nd = turn a ship, enter = fire / place,
#       clear = quit
import random
from ti_draw import clear, set_color, draw_text
from ti_draw import fill_rect as ti_fill_rect
try:
    from ti_draw import get_screen_dim
    SW, SH = get_screen_dim()
except:
    SW, SH = 319, 209

# Keep every box inside the screen and never stop the game over one box.
# The Evo draws boxes 1 pixel too small, so we ask for 1 pixel more.
def fill_rect(x, y, w, h):
    if x < 0:
        w, x = w + x, 0
    if y < 0:
        h, y = h + y, 0
    w, h = min(w, SW - x), min(h, SH - y)
    if w > 0 and h > 0:
        try:
            ti_fill_rect(x, y, w + 1, h + 1)
        except:
            pass
# Draw in a hidden buffer and show the finished picture at once: no flicker
try:
    from ti_draw import use_buffer, paint_buffer
    use_buffer()
except:
    paint_buffer = None
try:
    from ti_system import get_key as read_key
except:
    from ti_system import getKey as read_key
# On the Evo get_key wants one number. Find out once at the start.
try:
    read_key()
    key = read_key
except TypeError:
    def key():
        return read_key(0)
try:
    from ti_system import store_list, recall_list
except:
    store_list = recall_list = None
try:
    from time import sleep
except:
    from ti_system import sleep
try:
    import gc
except:
    gc = None

LEFT = (2, 24)
RIGHT = (1, 26)
UP = (3, 25)
DOWN = (4, 34)
OK = (5, 105)                 # enter
SECOND = (21, 22)             # 2nd, mode
QUIT = (9, 45)                # clear
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (150, 150, 150)
YELLOW = (255, 220, 0)

def paint():
    if paint_buffer:
        paint_buffer()

def write(x, y, s):                    # text that can never stop the game
    try:
        draw_text(x, y, s)
    except:
        pass

def wait_for(keys):
    paint()
    while True:
        k = key()
        if k in keys:
            return k
        sleep(0.05)

# Numbers saved in a calculator list, so they stay after quitting
def load(name, n):
    try:
        l = [int(v) for v in recall_list(name)]
    except:
        l = []
    return (l + [0] * n)[:n]

def save(name, l):
    try:
        store_list(name, l)
    except:
        pass

# Text panel on the right side: rows 30 px high, the whole row is wiped first
def text(row, s, col=WHITE):
    set_color(*BLACK)
    fill_rect(TX, row * 30, SW - TX, 29)
    set_color(*col)
    write(TX, row * 30 + 22, s)

def box_frame(x, y, w, h, t, col):     # a frame t pixels thick
    set_color(*col)
    fill_rect(x, y, w, t)
    fill_rect(x, y + h - t, w, t)
    fill_rect(x, y, t, h)
    fill_rect(x + w - t, y, t, h)

def title_screen(name, col, line):
    clear()
    set_color(*BLACK)
    fill_rect(0, 0, SW, SH)
    set_color(*col)
    write(SW // 2 - 80, 25, name)
    set_color(*WHITE)
    write(SW // 2 - 80, 55, line)

# A menu on the start screen. Returns the chosen number, or -1 for clear.
def menu(options, choice, hint):
    x = SW // 2 - 80
    set_color(*BLACK)
    fill_rect(0, 64, SW, SH - 64)
    set_color(*WHITE)
    write(x, 202, hint)
    while True:
        for i in range(len(options)):
            set_color(*BLACK)
            fill_rect(x - 20, 64 + i * 28, 230, 27)
            set_color(*(YELLOW if i == choice else GREY))
            write(x, 90 + i * 28, ("> " if i == choice else "  ") + options[i])
        k = wait_for(UP + DOWN + OK + QUIT)
        if k in QUIT:
            return -1
        if k in OK:
            return choice
        if k in UP:
            choice = (choice - 1) % len(options)
        if k in DOWN:
            choice = (choice + 1) % len(options)

N = 10
C = 14                        # square size
GX = (4, SW - 4 - N * C)      # left edge of your sea and of the enemy sea
GY = SH - N * C - 4
FLEET = [5, 4, 3, 3, 2]       # ship lengths
WATER = (0, 70, 160)
SHIP = (140, 140, 140)
HIT = (230, 0, 0)
SUNK = (110, 0, 0)
MISS = WHITE
FITS = YELLOW                 # a ship you are placing, where it fits
BAD = (255, 90, 90)           # ... where it would overlap another ship

class Sea:
    def __init__(self, auto):
        self.ship = [-1] * (N * N)        # ship number on each square, -1 = water
        self.shot = [0] * (N * N)         # 1 = already fired at
        self.left = list(FLEET)           # squares not yet hit, per ship
        if auto:                          # place the ships at random
            for s in range(len(FLEET)):
                while True:
                    down = random.random() < 0.5
                    r = random.randrange(N - (FLEET[s] - 1 if down else 0))
                    c = random.randrange(N - (0 if down else FLEET[s] - 1))
                    sq = cells(r, c, FLEET[s], down)
                    if self.free(sq):
                        self.add(sq, s)
                        break

    def free(self, sq):
        return all(self.ship[i] < 0 for i in sq)

    def add(self, sq, s):
        for i in sq:
            self.ship[i] = s

    def fire(self, i):                    # returns "miss", "hit" or "sunk"
        self.shot[i] = 1
        s = self.ship[i]
        if s < 0:
            return "miss"
        self.left[s] -= 1
        return "sunk" if self.left[s] == 0 else "hit"

    def lost(self):
        return sum(self.left) == 0

def cells(r, c, n, down):                 # squares of a ship
    return [(r + k) * N + c if down else r * N + c + k for k in range(n)]

def square(side, sea, i, show_ships, cursor=False, col=None):
    r, c = divmod(i, N)
    x, y = GX[side] + c * C, GY + r * C
    s = sea.ship[i]
    if col:
        pass                              # colour given (ship being placed)
    elif sea.shot[i] and s >= 0:
        col = SUNK if sea.left[s] == 0 else HIT
    elif s >= 0 and show_ships:
        col = SHIP
    else:
        col = WATER
    set_color(*col)
    fill_rect(x, y, C - 1, C - 1)
    if sea.shot[i] and s < 0:             # miss: small white dot
        set_color(*MISS)
        fill_rect(x + 5, y + 5, 3, 3)
    if cursor:
        box_frame(x, y, C - 1, C - 1, 2, YELLOW)

def draw_sea(side, sea, show):
    for i in range(N * N):
        square(side, sea, i, show)

def redraw_ship(side, sea, s, show):     # a sunk ship turns dark red
    for i in range(N * N):
        if sea.ship[i] == s:
            square(side, sea, i, show)

def message(s, col=WHITE):               # top line, full width
    set_color(*BLACK)
    fill_rect(0, 0, SW, 29)
    set_color(*col)
    write(6, 22, s)

def board_screen():
    clear()
    set_color(*BLACK)
    fill_rect(0, 0, SW, SH)
    set_color(*WHITE)

# Black screen between turns, so the players don't see each other's ships
def hand_over(p):
    clear()
    set_color(*BLACK)
    fill_rect(0, 0, SW, SH)
    set_color(*YELLOW)
    write(SW // 2 - 70, 80, "PLAYER " + str(p))
    set_color(*WHITE)
    write(SW // 2 - 70, 115, "Your turn.")
    write(SW // 2 - 70, 145, "ENTER: ready")
    return wait_for(OK + QUIT) in OK

# Let a player place the 5 ships. Returns False for quit.
def place_fleet(sea, who):
    board_screen()
    draw_sea(0, sea, True)
    write(GX[0], GY - 8, "Your sea")
    x = GX[1]
    for i, s in enumerate(["ARROWS: move", "2ND: turn", "ENTER: place", "CLEAR: quit"]):
        write(x, GY + 20 + i * 30, s)
    r, c, down = 0, 0, False
    for s in range(len(FLEET)):
        n = FLEET[s]
        message(who + "place ship (" + str(n) + ")")
        while True:
            r = min(r, N - n) if down else r      # keep the ship on the board
            c = c if down else min(c, N - n)
            sq = cells(r, c, n, down)
            ok = sea.free(sq)
            for i in sq:
                square(0, sea, i, True, False, FITS if ok else BAD)
            k = wait_for(LEFT + RIGHT + UP + DOWN + SECOND + OK + QUIT)
            for i in sq:                          # take the preview away
                square(0, sea, i, True)
            if k in QUIT:
                return False
            if k in OK and ok:
                sea.add(sq, s)
                for i in sq:
                    square(0, sea, i, True)
                break
            if k in LEFT:
                c = max(0, c - 1)
            elif k in RIGHT:
                c = min(N - 1, c + 1)
            elif k in UP:
                r = max(0, r - 1)
            elif k in DOWN:
                r = min(N - 1, r + 1)
            elif k in SECOND:
                down = not down
    return True

# One player sets up a fleet: chooses "myself" or "random". None = quit.
def setup(who):
    title_screen("BATTLESHIP", (0, 140, 255), who + "your ships")
    how = menu(["Place ships myself", "Random ships"], 0, "UP/DOWN + ENTER")
    if how < 0:
        return None
    sea = Sea(how == 1)
    if how == 0 and not place_fleet(sea, who):
        return None
    return sea

# Aim at a square of the enemy sea. Returns the square, or -1 for quit.
def aim(enemy, cur):
    square(1, enemy, cur, False, True)
    paint()
    while True:
        k = key()
        if not k:
            sleep(0.03)
            continue
        if k in QUIT:
            return -1
        old = cur
        r, c = divmod(cur, N)
        if k in LEFT:
            c = (c - 1) % N
        elif k in RIGHT:
            c = (c + 1) % N
        elif k in UP:
            r = (r - 1) % N
        elif k in DOWN:
            r = (r + 1) % N
        elif k in OK and not enemy.shot[cur]:
            return cur
        cur = r * N + c
        square(1, enemy, old, False)
        square(1, enemy, cur, False, True)
        paint()

def shoot(enemy, i):                     # fire and draw the result
    res = enemy.fire(i)
    if res == "sunk":
        redraw_ship(1, enemy, enemy.ship[i], False)
    square(1, enemy, i, False, True)
    return res

def battle_screen(mine, enemy):
    board_screen()
    draw_sea(0, mine, True)
    draw_sea(1, enemy, False)
    set_color(*WHITE)
    write(GX[0], GY - 8, "Your sea")
    write(GX[1], GY - 8, "Enemy sea")

# Computer aims: first at squares next to hits on ships that aren't sunk yet,
# otherwise at random squares on a chessboard pattern (every ship is at least 2 long)
def ai_target(sea):
    near = []
    for i in range(N * N):
        if sea.shot[i] and sea.ship[i] >= 0 and sea.left[sea.ship[i]] > 0:
            r, c = divmod(i, N)
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N and not sea.shot[rr * N + cc]:
                    near.append(rr * N + cc)
    if near:
        return random.choice(near)
    free = [i for i in range(N * N) if not sea.shot[i] and (i // N + i % N) % 2 == 0]
    if not free:
        free = [i for i in range(N * N) if not sea.shot[i]]
    return random.choice(free)

def game_cpu():                           # returns True win, False lose, None quit
    me = setup("")
    if me is None:
        return None
    cpu = Sea(True)
    battle_screen(me, cpu)
    cur = 44
    message("Aim and fire!")
    while True:
        while True:                       # your turn: a hit means fire again
            cur = aim(cpu, cur)
            if cur < 0:
                return None
            res = shoot(cpu, cur)
            if cpu.lost():
                return True
            if res == "miss":
                message("You: miss!")
                break
            message("You: " + res + "! Fire again", HIT)
        paint()
        sleep(0.7)
        while True:                       # the calculator's turn, same rule
            i = ai_target(me)
            res = me.fire(i)
            if res == "sunk":
                redraw_ship(0, me, me.ship[i], True)
            else:
                square(0, me, i, True)
            message("CPU: " + res + "!", HIT if res != "miss" else WHITE)
            if me.lost():
                return False
            if res == "miss":
                break
            paint()
            sleep(0.7)

def game_two():                           # returns 1 or 2 (winner), None quit
    seas = [None, None, None]
    for p in (1, 2):
        if not hand_over(p):
            return None
        seas[p] = setup("Player " + str(p) + ": ")
        if seas[p] is None:
            return None
    cur = [0, 44, 44]
    news = [0, "Aim and fire!", "Aim and fire!"]    # what happened to your sea
    p = 1
    while True:
        if not hand_over(p):
            return None
        mine, enemy = seas[p], seas[3 - p]
        battle_screen(mine, enemy)
        message(news[p])
        paint()
        shots = hits = 0
        while True:                       # a hit means fire again
            c = aim(enemy, cur[p])
            if c < 0:
                return None
            cur[p] = c
            res = shoot(enemy, c)
            shots += 1
            if enemy.lost():
                return p
            if res == "miss":
                break
            hits += 1
            message("P" + str(p) + ": " + res + "! Fire again", HIT)
        news[3 - p] = "Player " + str(p) + ": " + str(hits) + " hit" + ("" if hits == 1 else "s")
        message("P" + str(p) + ": miss!  ENTER: next")
        if wait_for(OK + QUIT) in QUIT:
            return None
        p = 3 - p

# --- start ---
stats = load("SHIPS", 4)                 # [wins, losses, player 1 wins, player 2 wins]
while True:
    title_screen("BATTLESHIP", (0, 140, 255),
                 "You " + str(stats[0]) + "-" + str(stats[1]) + "  P1 " + str(stats[2]) + "-" + str(stats[3]) + " P2")
    mode = menu(["1 player", "2 players"], 0, "UP/DOWN + ENTER")
    if mode < 0:
        break
    if mode == 0:
        won = game_cpu()
        if won is None:
            continue
        stats[0 if won else 1] += 1
        msg = "YOU WIN!" if won else "YOU LOSE"
    else:
        w = game_two()
        if w is None:
            continue
        stats[1 + w] += 1
        msg = "PLAYER " + str(w) + " WINS!"
    save("SHIPS", stats)
    message(msg + "  ENTER: menu", YELLOW)
    if wait_for(OK + QUIT) in QUIT:
        break
paint()
