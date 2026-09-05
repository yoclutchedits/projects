import streamlit as st
import random
from collections import deque
import random
from collections import deque
from streamlit_shortcuts import add_shortcuts

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

def maze_to_html(grid, player_pos, end, path=None):
    if path is None:
        path = []
    cell_size = 16  # pixels
    html = '<div style="display: grid; grid-template-columns: repeat({}, {}px); gap: 0px;">'.format(len(grid[0]), cell_size)
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if (x, y) == player_pos:
                color = "#3b82f6"
            elif (x, y) == end:
                color = "#22c55e" 
            elif (x, y) in path:
                color = "#facc15"
            elif cell == 0:
                color = "#1f2937"
            else:
                color = "#f9fafb"
            html += f'<div style="width:{cell_size}px; height:{cell_size}px; background-color:{color};"></div>'
    html += '</div>'
    return html
def maze_app(width, height):
    st.title("Maze Game")

    if "maze" not in st.session_state or st.session_state.get("maze_size") != (width, height):
        st.session_state.maze = generate_maze(width, height)
        st.session_state.maze_size = (width, height)
        st.session_state.start = (0, 0)
        st.session_state.move_count = 0
        st.session_state.end = (2 * (width - 1), 2 * (height - 1))
        st.session_state.player_pos = st.session_state.start
        if "solved_path" in st.session_state:
            del st.session_state.solved_path
    if st.session_state.player_pos == st.session_state.end:
        optimal = solve(st.session_state.maze, st.session_state.start, st.session_state.end)
        optimal_len = len(optimal) - 1 if optimal else "?"
        st.success(f"You won in {st.session_state.move_count} moves! Optimal was {optimal_len}.")
    with st.sidebar:
        st.write("---")
        st.title("Useful Settings")
    if st.sidebar.button("Solve for me"):
        st.session_state.solved_path = solve(st.session_state.maze, st.session_state.start, st.session_state.end)
    if st.sidebar.button("New Maze"):
        del st.session_state.maze
        del st.session_state.player_pos
        del st.session_state.move_count
        if "solved_path" in st.session_state:
            del st.session_state.solved_path
        st.rerun()

    maze_html = maze_to_html(
    st.session_state.maze,
    st.session_state.player_pos,
    st.session_state.end,
    st.session_state.get("solved_path", [])
)
    st.markdown(maze_html, unsafe_allow_html=True)
    _, _, col_w, _, _ = st.columns([2, 1, 1, 1, 2])
    with col_w:
        if st.button("Forward(W)", key="btn_forward"):
            new_pos = can_move(st.session_state.maze, st.session_state.player_pos, "forward")
            if new_pos:
                st.session_state.player_pos = new_pos
                st.session_state.move_count += 1
            st.rerun()
    _, col_a, col_s, col_d, _ = st.columns([2, 1, 1, 1, 2])
    with col_a:
        if st.button("Left(A)", key="btn_left"):
            new_pos = can_move(st.session_state.maze, st.session_state.player_pos, "left")
            if new_pos:
                st.session_state.player_pos = new_pos
                st.session_state.move_count += 1
            st.rerun()
    with col_s:
        if st.button("Backward(S)", key="btn_backward"):
            new_pos = can_move(st.session_state.maze, st.session_state.player_pos, "backward")
            if new_pos:
                st.session_state.player_pos = new_pos
                st.session_state.move_count += 1
            st.rerun()
    with col_d:
        if st.button("Right(D)", key="btn_right"):
            new_pos = can_move(st.session_state.maze, st.session_state.player_pos, "right")
            if new_pos:
                st.session_state.player_pos = new_pos
                st.session_state.move_count += 1
            st.rerun()
    add_shortcuts(
        btn_forward="w",
        btn_backward="s",
        btn_left="a",
        btn_right="d",
    )
if __name__ == "__main__":
    st.title("Maze Game")
    difficulty = st.selectbox("Difficulty", ["Easy (10x10)", "Normal (20x20)", "Hard (30x30)"])
    sizes = {"Easy (10x10)": 10, "Normal (20x20)": 20, "Hard (30x30)": 30}
    size = sizes[difficulty]
    maze_app(size, size)