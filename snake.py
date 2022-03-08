from collections import deque
import heapq
import random
import sys

import pygame as pg
import tkinter as tk
from tkinter import messagebox

from colors import COLORS

SCREEN_WIDTH = 601
SCREEN_HEIGHT = 601
ROWS = 40
UP = (0,-1)
RIGHT = (1,0)
LEFT = (-1,0)
DOWN = (0,1)

DIR_MAP = {
    pg.K_RIGHT: RIGHT,
    pg.K_LEFT: LEFT,
    pg.K_UP: UP,
    pg.K_DOWN: DOWN
}
REV_MAP = {
    (0,-1): UP,
    (1,0): RIGHT,
    (-1,0): LEFT,
    (0,1): DOWN,
}

class Snake:
    def __init__(cls, grid, board):
        cls.board = board
        cls.grid = grid
        cls.head = grid[20][20]
        cls.body = deque()
        grid[20][20].set_status("SNAKE")
        cls.dir = UP
        cls.ate = False

    def reset(cls):
        cls.head = cls.grid[20][20]
        cls.body = deque()
        cls.grid[20][20].set_status("SNAKE")
        cls.dir = UP
        cls.ate = False

    def move(cls):
        d_row, d_col = cls.dir
        row, col = cls.head.pos
        next_row = row + d_row
        next_col = col + d_col
        if not cls.valid_move(next_row, next_col):
            if messagebox.askquestion(title="Dead", message=f"Score: {len(cls.body) + 1}\nStart again?") == "yes":
                cls.board.reset()
            else:
                pg.quit()
                sys.exit()
            return

        new_head = cls.grid[next_row][next_col]
        if new_head.is_food():
            cls.ate = True

        if not cls.body and not cls.ate:
            cls.head.reset()
        else:
            cls.body.append(cls.head)
        
        if cls.body and not cls.ate:
            cls.body.popleft().reset()
        
        cls.head = new_head
        cls.head.set_status("SNAKE")

    def valid_move(cls, row, col):
        return (
            0 <= row < len(cls.grid)
            and 0 <= col < len(cls.grid[0])
            and not cls.grid[row][col].is_snake()
        )
        

class Cell:
    def __init__(cls, row, col, w):
        cls.row = row
        cls.col = col
        cls.x = w * row
        cls.y = w * col
        cls.width = w
        cls.status = None
        cls.rect = None
        cls.color = COLORS["BACKGROUND"]

    @property
    def pos(cls):
        return (cls.row, cls.col)

    def reset(cls):
        cls.status = None
        cls.color = COLORS["BACKGROUND"]

    def set_color(cls, color):
        cls.color = COLORS[color] if color in COLORS else COLORS["BACKGROUND"]

    def set_status(cls, status):
        cls.status = status
        cls.set_color(status)

    def draw(cls, screen):
        cls.rect = pg.draw.rect(screen, cls.color, (cls.x, cls.y, cls.width, cls.width) )

    def is_snake(cls):
        return cls.status == "SNAKE"

    def is_food(cls):
        return cls.status == "FOOD"

    def get_edges(cls, grid):
        coords = ( (0,1), (1,0), (0,-1), (-1,0) )
        edges = []
        row, col = cls.pos
        for d_row, d_col in coords:
            n_row = row + d_row
            n_col = col + d_col
            if (0 <= n_row < len(grid) 
                and 0 <= n_col < len(grid[0]) 
                and grid[n_row][n_col].status != "SNAKE"):
                edges.append(grid[n_row][n_col])
        return edges



    

class GameBoard:
    def __init__(cls, width, height, rows):
        cls.width = width
        cls.height = height
        cls.rows = rows
        cls.grid = cls.make_grid()
        cls.snake = Snake(cls.grid, cls)
        cls.screen = pg.display.set_mode( (width,height) )
        pg.display.set_caption("Snake")
        cls.food = None


    def reset(cls):
        for row in cls.grid:
            for cell in row:
                cell.reset()

        cls.snake.reset()
        cls.place_food()


    @property
    def cell_width(cls):
        return cls.width // cls.rows

    def place_food(cls):
        cls.snake.ate = False
        food_cell = cls.get_random_cell()
        while food_cell.status:
            food_cell = cls.get_random_cell()

        food_cell.set_status("FOOD")
        cls.food = food_cell

    def get_random_cell(cls):
        return cls.grid[random.randint(0, len(cls.grid)-1)][random.randint(0, len(cls.grid[0])-1)]


    def make_grid(cls):
        grid = []
        for i in range(cls.rows):
            grid.append([])
            for j in range(cls.rows):
                grid[i].append( Cell(i, j, cls.cell_width) )
        return grid

    def draw_grid(cls):
        for i in range(ROWS + 1):
            x = i * cls.cell_width
            y = i * cls.cell_width
            pg.draw.line(cls.screen, COLORS["LINE"], (x, 0), (x, cls.width) )
            pg.draw.line(cls.screen, COLORS["LINE"], (0, y), (cls.width, y) )

    def draw(cls):
        cls.screen.fill(COLORS["BACKGROUND"])
        
        for row in cls.grid:
            for cell in row:
                cell.draw(cls.screen)

        cls.draw_grid()
        pg.display.update()

class AutoPlayer:
    def __init__(cls, board):
        cls.board = board
        cls.snake = board.snake
        cls.path = None

    def auto_move(cls):
        if not cls.path:
            cls.path = cls.a_star(cls.snake.head, cls.board.food)

        if cls.path:
            nrow, ncol = cls.path.pop().pos
            row, col = cls.snake.head.pos
            d_row = nrow - row
            d_col = ncol - col
            cls.snake.dir = REV_MAP[(d_row, d_col)]


    def construct_path(cls, preceding, start, end):
        curr = end
        path = []
        while curr in preceding:
            path.append(curr)
            curr = preceding[curr]

        return path

    def h(cls, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return (abs(x1 - x2) + abs(y1 - y2)) * 2

    def a_star(cls, start, end):
        grid = cls.board.grid
        count = 0
        open_q = [ (0, count, start) ]
        in_open = { start }
        preceding = {}
        g_scores = { cell: float('inf') for row in grid for cell in row }
        g_scores[start] = 0
        f_scores = { cell: float('inf') for row in grid for cell in row }
        f_scores[start] = cls.h(start.pos, end.pos)

        while open_q:
            curr = heapq.heappop(open_q)[2]
            in_open.remove(curr)
            if curr == end:
                return cls.construct_path(preceding, start, end)

            for edge in curr.get_edges(grid):
                tmp_g = g_scores[curr] + 1
                if tmp_g < g_scores[edge]:
                    preceding[edge] = curr
                    g_scores[edge] = tmp_g
                    f_scores[edge] = tmp_g + cls.h(edge.pos, end.pos)
                    if edge not in in_open:
                        count += 1
                        heapq.heappush( open_q, (f_scores[edge], count, edge) )
                        in_open.add(edge)

        return None

if __name__ == "__main__":
    tk_root = tk.Tk()
    tk_root.withdraw()
    screen = pg.display.set_mode( (SCREEN_WIDTH, SCREEN_HEIGHT) )
    clock = pg.time.Clock()
    board = GameBoard(SCREEN_WIDTH, SCREEN_HEIGHT, ROWS)
    snake = board.snake
    board.place_food()
    player = AutoPlayer(board)

    running = True
    while running:
        board.draw()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN:
                if event.key in DIR_MAP:
                    snake.dir = DIR_MAP[event.key]
        player.auto_move()
        snake.move()
        if snake.ate:
            board.place_food()
        
        clock.tick(100)
 
    pg.quit()


        