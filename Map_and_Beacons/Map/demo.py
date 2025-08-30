import pygame
import heapq

# Map definition: 0 = free, 1 = wall
GRID = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0, 0, 1, 1, 1, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 1, 0, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 0, 1, 0, 1, 0],
    [0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 1, 1, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 1, 1, 0],
]

CELL_SIZE = 60
ROWS, COLS = len(GRID), len(GRID[0])
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE

# Colors
COLOR_BG = (30, 30, 30)
COLOR_GRID = (50, 50, 50)
COLOR_WALL = (100, 100, 100)
COLOR_CROWD = (255, 0, 0)
COLOR_SELL = (0, 255, 0)
COLOR_START = (0, 0, 255)
COLOR_END = (255, 255, 0)
COLOR_PATH = (0, 255, 255)
COLOR_TEXT = (200, 200, 200)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Interactive A* Path Finder")
font = pygame.font.SysFont(None, 24)

# User-selectable points
crowded_points = set()
selling_points = set()
start_point = None
end_point = None
mode = 'crowd'  # 'crowd', 'sell', 'start', 'end'
path = None
loading = False

# PathFinder class
class PathFinder:
    def __init__(self, grid, selling_points, crowded_points):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.selling_points = set(selling_points)
        self.crowded_points = set(crowded_points)

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.rows and 0 <= pos[1] < self.cols

    def is_walkable(self, pos):
        return self.grid[pos[0]][pos[1]] == 0

    def astar(self, start, end):
        class Node:
            def __init__(self, position, parent=None):
                self.position = position
                self.parent = parent
                self.g = 0
                self.h = 0
                self.f = 0
            def __lt__(self, other):
                return self.f < other.f

        open_list = []
        closed_set = set()
        heapq.heappush(open_list, Node(start))

        while open_list:
            current = heapq.heappop(open_list)
            if current.position == end:
                path = []
                while current:
                    path.append(current.position)
                    current = current.parent
                return path[::-1]

            closed_set.add(current.position)
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nxt = (current.position[0]+dx, current.position[1]+dy)
                if not self.in_bounds(nxt) or not self.is_walkable(nxt) or nxt in closed_set:
                    continue
                neighbor = Node(nxt, current)
                penalty = 10 if nxt in self.crowded_points else 1
                neighbor.g = current.g + penalty
                neighbor.h = self.heuristic(nxt, end)
                neighbor.f = neighbor.g + neighbor.h
                if any(n.position == nxt and n.f <= neighbor.f for n in open_list):
                    continue
                heapq.heappush(open_list, neighbor)
        return None

    def find_path(self, start, end):
        best = None
        for sp in self.selling_points:
            p1 = self.astar(start, sp)
            p2 = self.astar(sp, end)
            if p1 and p2:
                full = p1[:-1] + p2
                cost = len(full)
                if best is None or cost < best[0]:
                    best = (cost, full)
        return best[1] if best else None

# Draw functions
def draw_grid():
    for i in range(ROWS):
        for j in range(COLS):
            rect = pygame.Rect(j*CELL_SIZE, i*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if GRID[i][j] == 1:
                pygame.draw.rect(screen, COLOR_WALL, rect)
            else:
                pygame.draw.rect(screen, COLOR_GRID, rect, 1)

def draw_points():
    for p in crowded_points:
        rect = pygame.Rect(p[1]*CELL_SIZE, p[0]*CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, COLOR_CROWD, rect)
    for p in selling_points:
        rect = pygame.Rect(p[1]*CELL_SIZE, p[0]*CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, COLOR_SELL, rect)
    if start_point:
        rect = pygame.Rect(start_point[1]*CELL_SIZE, start_point[0]*CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, COLOR_START, rect)
    if end_point:
        rect = pygame.Rect(end_point[1]*CELL_SIZE, end_point[0]*CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, COLOR_END, rect)

def draw_path():
    if path:
        # Make the path more visible with thicker lines
        for i in range(len(path) - 1):
            start_pos = (path[i][1] * CELL_SIZE + CELL_SIZE // 2, path[i][0] * CELL_SIZE + CELL_SIZE // 2)
            end_pos = (path[i+1][1] * CELL_SIZE + CELL_SIZE // 2, path[i+1][0] * CELL_SIZE + CELL_SIZE // 2)
            pygame.draw.line(screen, COLOR_PATH, start_pos, end_pos, 5)
        
        # Draw points along the path
        for p in path:
            rect = pygame.Rect(p[1]*CELL_SIZE+CELL_SIZE//4, p[0]*CELL_SIZE+CELL_SIZE//4, CELL_SIZE//2, CELL_SIZE//2)
            pygame.draw.rect(screen, COLOR_PATH, rect)

def draw_text(text, position):
    img = font.render(text, True, COLOR_TEXT)
    screen.blit(img, position)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                mode = 'crowd'
            elif event.key == pygame.K_2:
                mode = 'sell'
            elif event.key == pygame.K_3:
                mode = 'start'
            elif event.key == pygame.K_4:
                mode = 'end'
            elif event.key == pygame.K_r and start_point and end_point and selling_points:
                loading = True
                # Show loading indicator
                screen.fill(COLOR_BG)
                draw_grid()
                draw_points()
                draw_text('Loading path...', (WIDTH//2 - 60, HEIGHT//2))
                pygame.display.flip()
                
                try:
                    pf = PathFinder(GRID, selling_points, crowded_points)
                    path = pf.find_path(start_point, end_point)
                    if not path:
                        # Add debug message if path calculation failed
                        print("No path found between start and end points")
                except Exception as e:
                    print(f"Error calculating path: {e}")
                
                loading = False
                # Force screen update after path calculation
                screen.fill(COLOR_BG)
                draw_grid()
                draw_points()
                draw_path()
                pygame.display.flip()
                
        elif event.type == pygame.MOUSEBUTTONDOWN and not loading:
            x, y = pygame.mouse.get_pos()
            row, col = y // CELL_SIZE, x // CELL_SIZE
            if 0 <= row < ROWS and 0 <= col < COLS and GRID[row][col] == 0:  # Check valid position
                if mode == 'crowd':
                    if (row, col) in crowded_points:
                        crowded_points.remove((row, col))
                    else:
                        crowded_points.add((row, col))
                    path = None
                elif mode == 'sell':
                    if (row, col) in selling_points:
                        selling_points.remove((row, col))
                    else:
                        selling_points.add((row, col))
                    path = None
                elif mode == 'start':
                    start_point = (row, col)
                    path = None
                elif mode == 'end':
                    end_point = (row, col)
                    path = None

    screen.fill(COLOR_BG)
    draw_grid()
    draw_points()
    draw_path()  # Make sure path is drawn
    
    # Display status messages
    if loading:
        draw_text('Loading path...', (WIDTH//2 - 60, HEIGHT//2))
    elif path:
        draw_text(f'Path found! Length: {len(path)}', (WIDTH//2 - 100, 10))
    elif not path and start_point and end_point and selling_points:
        draw_text('Press R to compute path', (WIDTH//2 - 100, HEIGHT//2))

    draw_text(f"Mode: {mode}   (1:crowd,2:sell,3:start,4:end, R:run)", (10, HEIGHT - 30))
    pygame.display.flip()

pygame.quit()
