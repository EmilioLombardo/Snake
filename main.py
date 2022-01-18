from os import chdir as cd
import sys
import random
from numpy import array

import pygame

PROGRAM_DIR = "/Users/emiliolombardo/Documents/PythonGreier/Snake/"
cd(PROGRAM_DIR)

COLS = 10
ROWS = 10

WIDTH = 500
HEIGHT = WIDTH * (ROWS // COLS)
CELL_W = WIDTH // COLS

class Text:
    margin = 40
    row_h = HEIGHT//8

    def get_pos(cls, column, row, text_w):
        """
        Returns pixel coords for positioning text in given column and row.
        """

        x = {"left": cls.margin,
             "centre": (WIDTH - text_w)//2,
             "right": WIDTH - cls.margin - text_w
             }[column]
        y = cls.row_h * row

        return x, y

    def __init__(self, text, font, text_col, column, row):

        self.text = text
        self.font = font
        self.text_col = text_col

        self.column = column # "left", "right" or "centre"
        self.row = row

        self.render = self.font.render(self.text, True, self.text_col)

    def display(self, dest_surf, bg, new_text=None):
        """Method to blit text to a surface. Returns dirty rect."""

        w = self.render.get_width()

        if new_text is not None:
            new_render = self.font.render(new_text, True, self.text_col)
            self.text = new_text
            # Make sure text rect is wide enough to overwrite preexisting text
            w = max(w, new_render.get_width())

        else:
            new_render = self.font.render(self.text, True, self.text_col)

        self.render = new_render

        pos = self.get_pos(self.column, self.row, w)

        h = self.render.get_height()

        text_rect = (*pos, w, h)

        # Draw bg over text (bg can be a pygame surface or a solid colour)
        if type(bg) is pygame.Surface:
            bg_surf = bg
            dest_surf.set_clip(text_rect)
            dest_surf.blit(bg_surf, (0, 0))
            dest_surf.set_clip()

        elif type(bg) in [tuple, list] and len(bg) == 3:
            bg_colour = bg
            pygame.draw.rect(dest_surf, bg_colour, text_rect)

        else:
            raise Exception("bg argument not valid: "
                    + "bg must be either a pygame surface or an RGB colour")

        # Draw text
        dest_surf.blit(self.render, pos)

        return text_rect

    def clear(self, dest_surf, bg_surf):
        """Method to clear text from surface. Returns dirty rect."""

        w = self.render.get_width()
        h = self.render.get_height()
        pos = self.get_pos(self.column, self.row, w)

        rect = (*pos, w, h)

        # Draw bg over text
        dest_surf.set_clip(rect)
        dest_surf.blit(bg_surf, rect)
        dest_surf.set_clip()

        return rect


pygame.mixer.pre_init(buffer=32)
pygame.init()

BLACK = (10, 10, 10)
WHITE = (250, 250, 250)
GREY = (60, 60, 60)
BLUE = (80, 110, 255)
RED = (255, 50, 50)
GREEN = (64, 222, 106)
DARK_GREEN = (49, 189, 86) # Unused

UP_KEYS = [pygame.K_UP, pygame.K_w, pygame.K_i]
LEFT_KEYS = [pygame.K_LEFT, pygame.K_a, pygame.K_j]
DOWN_KEYS = [pygame.K_DOWN, pygame.K_s, pygame.K_k]
RIGHT_KEYS = [pygame.K_RIGHT, pygame.K_d, pygame.K_l]
RETRY_KEYS = [pygame.K_r]
PAUSE_KEYS = [pygame.K_SPACE, pygame.K_RETURN]
CONFIRM_KEYS = [pygame.K_SPACE, pygame.K_RETURN]

trills = [pygame.mixer.Sound(f"sfx/Trill_SFX/trill_{i}.mp3")
          for i in range(1, 9)]
game_over_sound = pygame.mixer.Sound(f"sfx/game_over.mp3")
perfect_score_sound = pygame.mixer.Sound(f"sfx/perfect_score.mp3")
pause_sound = pygame.mixer.Sound(f"sfx/pause.mp3")
resume_sound = pygame.mixer.Sound(f"sfx/resume.mp3")
normal_start_sound = pygame.mixer.Sound(f"sfx/start_normal.mp3")
fast_start_sound = pygame.mixer.Sound(f"sfx/start_fast.mp3")

DELTA = (
    array((0, -1)), # 0: Up
    array((-1, 0)), # 1: Left
    array((0, 1)), # 2: Down
    array((1, 0)) # 3: Right
    )

DELTA_LIST = [list(arr) for arr in DELTA]

FPS = 60
clock = pygame.time.Clock()

flags = pygame.DOUBLEBUF
screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
pygame.display.set_caption("Snake")

bg = pygame.Surface((screen.get_height(), screen.get_width()))
bg_colour = BLACK
bg.fill(bg_colour)

screen.blit(bg, (0, 0))

def cell(grid_x, grid_y):
    """Returns cell number given grid coordinates."""

    c = grid_x + grid_y * COLS
    return c

def pos(cell_num):
    """Returns grid coordinates given cell number."""

    c = cell_num

    if c is None:
        return None

    x = c % COLS
    y = c // COLS
    return array((x, y))

def step(starting_cell, *dir_list):
    """Starting from starting_cell and moving through the step(s) in dir_list,
    returns the cell at the resulting destination."""
    c = starting_cell
    if pos(c) is None:
        return None

    for d in dir_list:
        x, y = pos(c)
        new_x, new_y = array((x, y)) + DELTA[d]

        # If new coordinates are out of bounds, return None
        if new_x < 0 or new_x >= COLS:
            return None

        if new_y < 0 or new_y >= ROWS:
            return None

        c = cell(new_x, new_y)

    return c
    # return cell(new_x, new_y)

def pixel_pos(c):
    """Returns screen coordinates given cell number."""

    grid_x, grid_y = pos(c)
    pixel_x, pixel_y = grid_x * CELL_W, grid_y * CELL_W
    return array((pixel_x, pixel_y))

def draw_cell(dest_surf, c, connections=None, colour=WHITE):
    """Draws a rectangle at position in grid (given by cell number)."""

    x0, y0 = pixel_pos(c)
    cell_rect = (x0, y0, CELL_W, CELL_W)

    if connections is not None:
        margin = CELL_W // 6
        w = CELL_W - 2 * margin

        top_rect = (x0 + margin, y0, w, margin)
        left_rect = (x0, y0 + margin, margin, w)
        bottom_rect = (x0 + margin, y0 + margin + w, w, margin)
        right_rect = (x0 + margin + w, y0 + margin, margin, w)

        if 0 in connections: pygame.draw.rect(dest_surf, colour, top_rect)
        if 1 in connections: pygame.draw.rect(dest_surf, colour, left_rect)
        if 2 in connections: pygame.draw.rect(dest_surf, colour, bottom_rect)
        if 3 in connections: pygame.draw.rect(dest_surf, colour, right_rect)

        central_rect = (x0 + margin, y0 + margin, w, w)
        pygame.draw.rect(dest_surf, colour, central_rect)

    else:
        pygame.draw.rect(dest_surf, colour, cell_rect)

    return cell_rect

def menu(speed, muted):
    pygame.mouse.set_visible(True)
    pygame.display.set_caption("Snake")

    bg_colour = BLACK
    btn_text_col = WHITE

    title_font = pygame.font.Font("RussoOne-Regular.ttf", 80)
    medium_font = pygame.font.Font("RussoOne-Regular.ttf", 30)

    title_text = Text("SNAKE", title_font, GREEN, "centre", 1)

    normal_mode_btn = Text("NORMAL SPEED", medium_font, WHITE, "centre", 3)
    fast_mode_btn = Text("SUPER SPEED", medium_font, WHITE, "centre", 4)

    bg.fill(bg_colour)
    screen.blit(bg, (0, 0))

    normal_btn_rect = normal_mode_btn.display(screen, bg_colour)
    fast_btn_rect = fast_mode_btn.display(screen, bg_colour)

    def cursor_pos(text_rect, size=10, pos="left"):
        if type(text_rect) != pygame.Rect:
            text_rect = pygame.Rect(text_rect)

        if pos == "left":
            midleft = text_rect.midleft
            p1 = midleft[0] - size, midleft[1]
            p2 = array(p1) + array((-size, -size/2))
            p3 = array(p1) + array((-size, size/2))

        elif pos == "right":
            midright = text_rect.midright
            p1 = midright[0] + size, midright[1]
            p2 = array(p1) + array((size, -size/2))
            p3 = array(p1) + array((size, size/2))


        return p1, p2, p3

    def update_display():
        screen.blit(bg, (0, 0))

        title_text.display(screen, bg_colour)
        normal_mode_btn.display(screen, bg_colour)
        fast_mode_btn.display(screen, bg_colour)
        if speed == "normal":
            pygame.draw.polygon(screen, BLUE, cursor_pos(normal_btn_rect,
                                                         pos="left"))
            pygame.draw.polygon(screen, BLUE, cursor_pos(normal_btn_rect,
                                                         pos="right"))
        elif speed == "fast":
            pygame.draw.polygon(screen, BLUE, cursor_pos(fast_btn_rect,
                                                         pos="left"))
            pygame.draw.polygon(screen, BLUE, cursor_pos(fast_btn_rect,
                                                         pos="right"))

        pygame.display.flip()

    on_menu_screen = 1
    while on_menu_screen:
        events = pygame.event.get()

        if speed == "normal":
            normal_mode_btn.text_col = BLUE
            fast_mode_btn.text_col = WHITE

        elif speed == "fast":
            fast_mode_btn.text_col = BLUE
            normal_mode_btn.text_col = WHITE

        for e in events:
            etype = e.type
            if etype == pygame.KEYDOWN:
                key = e.key
            else:
                key = None

            if etype == pygame.QUIT or key == pygame.K_ESCAPE:
                on_menu_screen = 0
                sys.exit()
                return

            if key in UP_KEYS + DOWN_KEYS:
                if speed == "normal":
                    speed = "fast"
                else:
                    speed = "normal"

            if key in CONFIRM_KEYS:
                game_start(speed, muted)

        clock.tick(FPS)
        update_display()

def game_start(speed, muted):

    bg_colour = BLACK
    frame_counter = 0

    if speed == "normal":
        MVMT_FPC = 10 # "FPC" stands for "frames per cell"
    elif speed == "fast":
        MVMT_FPC = 6

    mvmt_bonus_delay = 0 # Controls extra time given to move before crashing
    mvmt_timer = MVMT_FPC # Decrements by 1 each frame before resetting
                          # Snake moves forward when mvmt_timer reaches 0

    dir_buffer = []

    # Snake starts in the centre of the grid
    snake = [cell(COLS // 2 - 1, ROWS // 2 - 1)]

    valid_spots = [c for c in list(range(0, COLS*ROWS))
                   if c not in snake]
    food_cell = random.choice(valid_spots)

    d = None
    dead = False

    pygame.display.set_caption(f"Snake – ({len(snake)}/{COLS*ROWS})")

    def update_display(paused=False):
        bg.fill(bg_colour)
        screen.blit(bg, (0, 0))

        draw_cell(screen, food_cell, connections=[], colour=RED)

        colour = WHITE

        for i in range(len(snake)):
            connections = []
            c = snake[i]

            if i > 0:
                prev_c = snake[i - 1]
                connection_dir = list(pos(prev_c) - pos(c))
                connections.append(DELTA_LIST.index(connection_dir))

            if i < len(snake) - 1:
                next_c = snake[i + 1]
                connection_dir = list(pos(next_c) - pos(c))
                connections.append(DELTA_LIST.index(connection_dir))

            draw_cell(screen, c, connections, colour)

        if paused:
            draw_cell(screen, snake[-1], connections=[], colour=GREEN)

        pygame.display.flip()

    pygame.display.flip()

    if not muted:
        if speed == "normal":
            normal_start_sound.play()
        elif speed == "fast":
            fast_start_sound.play()

    paused = False

    in_game = True
    dead = False
    perfect_score = False
    while in_game:

        events = pygame.event.get()
        for e in events:
            etype = e.type
            if etype == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif etype == pygame.MOUSEMOTION:
                pygame.mouse.set_visible(True)
                continue

            elif etype != pygame.KEYDOWN:
                continue

            key = e.key

            if key == pygame.K_ESCAPE:
                menu(speed, muted)
                in_game = False
                break

            pygame.mouse.set_visible(False)

            if key in RETRY_KEYS:
                game_start(speed, muted)
                in_game = False
                break

            if dead and key in CONFIRM_KEYS:
                game_start(speed, muted)
                in_game = False
                break

            if key in PAUSE_KEYS:

                # Toggle pause
                paused = not paused

                if paused:
                    bg_colour = GREY
                    if not muted:
                        pause_sound.play()
                else:
                    bg_colour = BLACK
                    if not muted:
                        resume_sound.play()

            if key == pygame.K_m:
                # Toggle mute
                if not muted: pygame.mixer.stop()
                muted = not muted

            if paused:
                # Don't check directional inputs
                dir_buffer = []
                continue

            # --- Input/buffer movements --- #

            next_dir = dir_buffer[-1] if dir_buffer else d
            input_time = mvmt_timer

            if key in UP_KEYS and (d != 0 or next_dir != 0):
                dir_buffer.append((0, input_time))

            elif key in LEFT_KEYS and (d != 1 or next_dir != 1):
                dir_buffer.append((1, input_time))

            elif key in DOWN_KEYS and (d != 2 or next_dir != 2):
                dir_buffer.append((2, input_time))

            elif key in RIGHT_KEYS and (d != 3 or next_dir != 3):
                dir_buffer.append((3, input_time))

        if not in_game:
            break

        # --- Movement --- #

        # At the start of the game, wait for a directional input before moving
        if d is None:
            d, input_time = dir_buffer[0] if dir_buffer else (None, 1)
            prev_d = d

        elif mvmt_timer <= 0 and not (paused or dead):
            if dir_buffer:
                # Only keep the two last inputs in the buffer
                if len(dir_buffer) > 2:
                    dir_buffer = dir_buffer[-2:]

                # Make the next buffered input the next movement direction
                #   (...but not if it's the opposite of the current direction,
                #    since you shouldn't be able to move backwards.)
                for i in range(len(dir_buffer)):
                    buffered_dir, input_time = dir_buffer.pop(0)
                    if (buffered_dir + 2) % 4 != d:
                        d = buffered_dir
                        break

            curr_head = snake[-1]
            next_head = step(curr_head, d)

            invalid_spots = snake[1:] + ([next_head] if next_head is not None
                                         else [])

            valid_spots = [c for c in range(COLS*ROWS)
                           if c not in invalid_spots]

            if (mvmt_timer <= 0) and (input_time < MVMT_FPC//2) and (
                next_head in snake[1:]) and (
                step(curr_head, prev_d, d) not in snake[1:] + [None]) and (
                prev_d != d):
                # If about to crash into snake, but the crash could be avoided
                # by moving forward one more square before turning, then buffer
                # the right inputs to do so.
                # If the input is too early (input_time > MVMT_FPC//2), then
                # there will be no mercy.
                dir_buffer = [(prev_d, 1), (d, 1)]
                mvmt_bonus_delay = 0
                print(f"VÆR SÅ GOD!!!!")

            elif (mvmt_timer + mvmt_bonus_delay <= 0) and (
                next_head is None or
                next_head in snake[1:]):
                # If extra time delay has run out and snake crashes into
                # wall or itself

                dead = True

                if perfect_score:
                    bg_colour = BLUE
                    if not muted:
                        perfect_score_sound.play()
                else:
                    bg_colour = RED
                    if not muted:
                        game_over_sound.play()

            elif next_head is not None and next_head not in snake[1:]:
                # If not about to crash

                # Add cell in front of head to snake
                snake.append(next_head)

                # Reset movement timer
                mvmt_timer = MVMT_FPC

                if snake[-1] != food_cell:
                    # If snake isn't getting food, remove the backmost cell in
                    # snake (thus making it look like the snake has simply
                    # moved forward).
                    del snake[0]
                else:
                    # If snake has got the food, *don't* remove the backmost
                    # cell in the snake (thus making the snake longer in total).
                    if not muted: random.choice(trills).play()
                    # Move food to new spot
                    if not valid_spots:
                        perfect_score = True
                    else:
                        food_cell = random.choice(valid_spots)
                        pygame.display.set_caption(
                                f"Snake – ({len(snake)}/{COLS*ROWS})")

                # After having moved forwards, check if there is something to
                # crash into in front of the snake.
                c_in_front = step(snake[-1], d)
                if prev_d == d and (c_in_front is None or c_in_front in
                                    snake[1:]):
                    # If there is indeed something blocking the way,
                    # give extra time to change direction before next movement
                    mvmt_bonus_delay = MVMT_FPC // 2.5

        prev_d = d

        update_display(paused)

        if not paused: mvmt_timer -= 1
        frame_counter += 1
        clock.tick(FPS)

if len(sys.argv) == 1:
    muted = False
    print("Game sound is unmuted. Press M to toggle mute.")

elif sys.argv[1] in ["m", "muted", "mute", "0", "silent"]:
    muted = True
    print("Game sound is muted. Press M to toggle mute.")

else:
    muted = False
    print("Game sound is unmuted. Press M to toggle mute.")

menu("normal", muted)
# game_start("normal", False) ###
