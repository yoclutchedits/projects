import random
from collections import deque
import sys
import termios
import tty
import os
def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
        if key == "\x1b":
            key += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key
def generate_maze(width, height):
    grid_w = 2 * width + 1
    grid_h = 2 * height + 1
    grid = [[0 for _ in range(grid_w)] for _ in range(grid_h)]

    def carve(cx, cy):
        grid[cy][cx] = 1
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < grid_w and 0 <= ny < grid_h and grid[ny][nx] == 0:
                wallx= (cx+nx) // 2
                wally= (cy+ny) // 2
                grid[wally][wallx] = 1
                carve(nx,ny)
    carve(0, 0)
    return grid
def solve(grid, start, end):
    queue = deque([start])
    visited = {start}
    came_from = {}

    while queue:
        current = queue.popleft()
        if current == end:
            break
        cx, cy = current
        neighbors = [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]
        for nx, ny in neighbors:
            if 0 <= nx < len(grid[0]) and 0 <= ny < len(grid) and grid[ny][nx] == 1 and (nx, ny) not in visited:
                visited.add((nx, ny))
                came_from[(nx, ny)] = current
                queue.append((nx, ny))
    if end not in came_from and end != start:
        return None 
    path = []
    current = end
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path
def can_move(grid, pos, direction):
    x, y = pos
    deltas = {"forward": (0, -1), "backward": (0, 1), "left": (-1, 0), "right": (1, 0)}
    dx, dy = deltas[direction]
    nx, ny = x + dx, y + dy
    if 0 <= nx < len(grid[0]) and 0 <= ny < len(grid) and grid[ny][nx] == 1:
        return(nx,ny)
    return None
def print_maze_with_player(grid, player_pos, end):
    width = len(grid[0])
    print("┌" + "─" * width + "┐")  
    for y, row in enumerate(grid):
        line = ""
        for x, cell in enumerate(row):
            if (x,y) == player_pos:
                line += "P"
            elif (x,y) == end:
                line += "E"
            elif cell == 0:
                line += "|"
            else:
                line += " "
        print("│" + line + "│")
    print("└" + "─" * width + "┘")  
def play(grid, start, end):
    player_pos = start
    letter_to_direction = {
    "w": "forward",
    "s": "backward",
    "a": "left",
    "d": "right",
    "\x1b[A": "forward",
    "\x1b[B": "backward",
    "\x1b[C": "right",
    "\x1b[D": "left",
}
    while player_pos != end:
        print_maze_with_player(grid, player_pos, end)
        print("Move: w=forward, s=backward, a=left, d=right, e=exit")
        raw = get_key()
        cmd = raw.lower() if len(raw) == 1 else raw
        if cmd == "e":
            print("thanks for playing")
            print("here is the solve")
            path = solve(maze, start, end)
            print(path)
            break
        elif cmd in letter_to_direction:
            direction = letter_to_direction[cmd]
            new_pos = can_move(grid, player_pos, direction)
            if new_pos:
                player_pos = new_pos
                os.system("clear")
            else:
                print("Blocked by a wall!")
                os.system("clear")
        else:
            print("Unknown command.")
        if player_pos == end:
            print_maze_with_player(grid, player_pos, end)
            print("You won! 🎉")
if __name__=="__main__":
    print("Welcome!!🎉")
    print("select a difficulty easy(10x10)/normal(20x20)/hard(50x50)")
    sizes = {"easy": 10, "normal": 20, "hard": 50}
    choice = input(">").lower()
    if choice in sizes:
        size = sizes[choice]
        maze = generate_maze(size, size)
        end = (2 * (size - 1), 2 * (size - 1))
        try:
            play(maze, (0, 0), end)
        finally:
            os.system("stty sane")
else:
    print("Unknown difficulty.")
        
