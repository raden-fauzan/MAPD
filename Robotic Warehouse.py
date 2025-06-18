import pygame
import heapq
import math
import random

# Warna
WHITE = (255, 255, 255)
BLUE = (27, 38, 89)
GREY = (64, 64, 64)
RED = (190, 40, 50)
ORANGE = (255, 165, 0)
GREEN = (60, 220, 140)
GRIDC = (40, 40, 40)
BACKGROUND = (10, 10, 10)

# Layout Grid
MAP_GRID = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

# Ukuran
GRID_HEIGHT = len(MAP_GRID)
GRID_WIDTH = len(MAP_GRID[0])
CELL_SIZE = 50
MARGIN = 3
SCREEN_WIDTH = (CELL_SIZE + MARGIN) * GRID_WIDTH + MARGIN
SCREEN_HEIGHT = (CELL_SIZE + MARGIN) * GRID_HEIGHT + MARGIN

# Agen Pathfinding
def a_star_pathfinding(grid, start, end, dynamic_obstacles):
    class Node:
        def __init__(self, parent=None, position=None):
            self.parent=parent; self.position=position; self.g=0; self.h=0; self.f=0
        def __eq__(self, other): return self.position == other.position
        def __lt__(self, other): return self.f < other.f
    open_list=[]; closed_set=set(); start_node=Node(None, start); end_node=Node(None, end)
    heapq.heappush(open_list, start_node)
    while open_list:
        current_node=heapq.heappop(open_list)
        closed_set.add(current_node.position)
        if current_node.position == end_node.position:
            path=[]; current=current_node
            while current is not None: path.append(current.position); current=current.parent
            return path[::-1]
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            node_position=(current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])
            if not (0 <= node_position[0] < GRID_WIDTH and 0 <= node_position[1] < GRID_HEIGHT): continue
            if grid[node_position[1]][node_position[0]] == 1 and node_position != end: continue
            if node_position in dynamic_obstacles or node_position in closed_set: continue
            child=Node(current_node, node_position); child.g=current_node.g + 1
            child.h=abs(child.position[0] - end_node.position[0]) + abs(child.position[1] - end_node.position[1])
            child.f=child.g + child.h
            if not any(open_node for open_node in open_list if child == open_node and child.g >= open_node.g):
                heapq.heappush(open_list, child)
    return None

# Agen Delivery
class DeliveryAgent:
    def __init__(self, id, start_pos):
        self.id=id; self.pos=start_pos; self.path=[]; self.status="IDLE"
        self.task_pickup=None; self.task_dropoff=None
    def get_color(self):
        if self.status == "MENUJU_PICKUP": return RED
        elif self.status == "MENUJU_DROPOFF": return ORANGE
        else: return WHITE
    def set_task(self, pickup_loc, dropoff_loc, path_to_pickup):
        self.task_pickup=pickup_loc; self.task_dropoff=dropoff_loc; self.path=path_to_pickup[1:]
        self.status="MENUJU_PICKUP"; print(f"Robot {self.id}: Menerima tugas. Menuju rak {pickup_loc}...")
    def update(self, grid, other_agents_pos, dispatcher):
        if self.status == "IDLE": return
        if not self.path:
            if self.status == "MENUJU_PICKUP":
                print(f"Robot {self.id}: Tiba di rak {self.pos}. Mengambil barang.") 
                dispatcher.pickup_completed(self.pos); self.status="MENUJU_DROPOFF"
                print(f"Robot {self.id}: Mencari jalur ke drop-off {self.task_dropoff}...") 
                new_path=dispatcher.request_path(self.pos, self.task_dropoff, other_agents_pos)
                if new_path: self.path=new_path[1:]
                else: print(f"Robot {self.id}: GAGAL menemukan jalur ke drop-off."); self.status="IDLE" 
            elif self.status == "MENUJU_DROPOFF":
                print(f"Robot {self.id}: Barang berhasil diantar ke {self.pos}.") 
                task_assigned=dispatcher.assign_task_to_agent(self)
                if not task_assigned:
                    print(f"Robot {self.id}: Tidak ada tugas baru. (IDLE).") 
                    self.status="IDLE"; self.task_pickup=None; self.task_dropoff=None
            return
        next_pos=self.path[0]
        if next_pos in other_agents_pos: return
        self.pos=self.path.pop(0)
    def draw(self, screen):
        color=self.get_color()
        center_x=(MARGIN + CELL_SIZE) * self.pos[0] + MARGIN + CELL_SIZE // 2
        center_y=(MARGIN + CELL_SIZE) * self.pos[1] + MARGIN + CELL_SIZE // 2
        pygame.draw.circle(screen, color, (center_x, center_y), CELL_SIZE // 2 - 5)
        font=pygame.font.Font(None, 20); text=font.render(str(self.id), True, BACKGROUND)
        text_rect=text.get_rect(center=(center_x, center_y)); screen.blit(text, text_rect)

# Agen Dispatcher
class Dispatcher:
    def __init__(self, grid, rack_locs, dropoff_locs):
        self.grid = grid; self.agents = []; self.rack_locations = rack_locs; self.dropoff_locations = dropoff_locs
        self.active_racks = set(rack_locs)
        initial_tasks = list(rack_locs)
        random.shuffle(initial_tasks)
        self.tasks = initial_tasks
        print(f"Dispatcher: Total ada {len(self.tasks)} tugas.")
    def add_agent(self, agent): self.agents.append(agent)
    def pickup_completed(self, pickup_loc): self.active_racks.discard(pickup_loc); print(f"Dispatcher: Pickup di {pickup_loc} selesai.")
    def request_path(self, start, end, others_pos): return a_star_pathfinding(self.grid, start, end, others_pos)
    def assign_task_to_agent(self, agent):
        if not self.tasks: return False
        pickup_loc=self.tasks.pop(0)
        def distance(p1,p2): return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
        closest_dropoff=min(self.dropoff_locations,key=lambda d: distance(pickup_loc,d))
        print(f"Dispatcher: Menugaskan Robot {agent.id} untuk {pickup_loc} -> {closest_dropoff}") # --- PERUBAHAN ---
        other_agents_pos={a.pos for a in self.agents if a.id != agent.id}
        path=self.request_path(agent.pos, pickup_loc, other_agents_pos)
        if path: agent.set_task(pickup_loc, closest_dropoff, path); return True
        else: print(f"Dispatcher: Robot {agent.id} GAGAL menemukan jalur."); self.tasks.insert(0, pickup_loc); return False # --- PERUBAHAN ---
    def update(self):
        for agent in self.agents:
            if agent.status == "IDLE":
                if self.assign_task_to_agent(agent): break
        all_agent_positions={a.pos for a in self.agents}
        for agent in self.agents:
            other_positions=all_agent_positions - {agent.pos}
            agent.update(self.grid, other_positions, self)

# Fungsi Utama
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Warehouse Robot")
    clock = pygame.time.Clock()

    rack_positions=[]; dropoff_positions=[]
    for y,row in enumerate(MAP_GRID):
        for x,tile in enumerate(row):
            if tile == 1: rack_positions.append((x,y))
            elif tile == 2: dropoff_positions.append((x,y))
            
    dispatcher = Dispatcher(MAP_GRID, rack_positions, dropoff_positions)
    dispatcher.add_agent(DeliveryAgent(id=1, start_pos=dropoff_positions[0]))
    if len(dropoff_positions) > 1:
        dispatcher.add_agent(DeliveryAgent(id=2, start_pos=dropoff_positions[1]))
    
    running = True
    simulation_over = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and simulation_over:
                 pos = pygame.mouse.get_pos(); col = pos[0]//(CELL_SIZE+MARGIN); row = pos[1]//(CELL_SIZE+MARGIN)

        if not simulation_over:
            dispatcher.update()
            
            if not dispatcher.tasks and all(agent.status == "IDLE" for agent in dispatcher.agents):
                print("-" * 20)
                print("Semua barang sudah diantar.")
                print("-" * 20)
                simulation_over = True

        screen.fill(BACKGROUND)
        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                tile_type=MAP_GRID[row][col]; color=GRIDC
                if tile_type == 1:
                    color = BLUE if (col,row) in dispatcher.active_racks else WHITE
                elif tile_type == 2: color=GREY
                rect = pygame.Rect((MARGIN+CELL_SIZE)*col+MARGIN, (MARGIN+CELL_SIZE)*row+MARGIN, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, color, rect)

        for agent in dispatcher.agents:
            agent.draw(screen)

        if simulation_over:
            font = pygame.font.Font(None, 80)
            text = font.render("Simulasi Selesai", True, GREEN)
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            s = pygame.Surface((text.get_width() + 40, text.get_height() + 40))
            s.set_alpha(180)
            s.fill((0,0,0))
            screen.blit(s, (text_rect.left - 20, text_rect.top - 20))
            screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(5)

    pygame.quit()

if __name__ == '__main__':
    main()