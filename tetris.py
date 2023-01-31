import pygame
from collections import deque
import random
from copy import deepcopy
from enum import Enum

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)

class TetroType(Enum):
    I = 1
    J = 2
    L = 3
    O = 4
    S = 5
    Z = 6
    T = 7
    SHADOW = 8

class Tetromino:
    
    rotations = {
        TetroType.I : [[4, 5, 6, 7], [2, 6, 10, 14], [8, 9, 10, 11], [1, 5, 9, 13]],
        TetroType.J : [[0, 4, 5, 6], [1, 2, 5, 9], [4, 5, 6, 10], [1, 5, 8, 9]],
        TetroType.L : [[2, 4, 5, 6], [1, 5, 9, 10], [4, 5, 6, 8], [0, 1, 5, 9]],
        TetroType.O : [[1, 2, 5, 6]],
        TetroType.S : [[1, 2, 4, 5], [1, 5, 6, 10], [5, 6, 8, 9], [0, 4, 5, 9]],
        TetroType.Z : [[0, 1, 5, 6], [2, 5, 6, 9], [4, 5, 9, 10], [1, 4, 5, 8]],
        TetroType.T : [[1, 4, 5, 6], [1, 5, 6, 9], [4, 5, 6, 9], [1, 4, 5, 9]],
    }
    
    colors = {
        TetroType.I : (0, 255, 255),
        TetroType.J : (0, 0, 255),
        TetroType.L : (255, 127, 0),
        TetroType.O : (255, 255, 0),
        TetroType.S : (0, 255, 0),
        TetroType.Z : (255, 0, 0),
        TetroType.T : (128, 0, 128),
        TetroType.SHADOW : GRAY
    }
    
    def __init__(self, type, is_shadow=False):
        self.type = type
        self.is_shadow = is_shadow
        self.color = GRAY if is_shadow else self.colors[self.type] 
        self.rotation = 0
        self.x = 3
        self.y = 0
        self.next = None
    
    def image(self):
        return self.rotations[self.type][self.rotation]
    
    def rotate(self, rotation_type):
        self.rotation = (self.rotation + rotation_type) % len(self.rotations[self.type])

            
class Tetris:
    height = 22
    width = 10
    x = 100
    y = 20
    zoom = 20
    next_zoom = zoom / 2
    PRESSING_BOUND = 300
    fps = 10000
    score_table = {
        "Double" : 1,
        "Triple" : 2,
        "Tetris" : 4,
        "TSM" : 1,
        "TSS" : 2,
        "TSD" : 4,
        "TST" : 6,
        "b2b Tetris" : 6,
        "b2b TSM" : 2,
        "b2b TSS" : 3,
        "b2b TSD" : 6,
        "b2b TST" : 9,
    }
    
    wall_kick = [
        [(0, 0), ( 0, 0), ( 0, 0), ( 0, 0), ( 0, 0)],
        [(0, 0), (+1, 0), (+1, -1), ( 0,+2), (+1,+2)],
        [(0, 0), ( 0, 0), ( 0, 0), ( 0, 0), ( 0, 0)],
        [(0, 0), (-1, 0), (-1, -1), ( 0,+2), (-1,+2)],
    ]

    I_wall_kick = [
        [( 0, 0), (-1, 0), (+2, 0), (-1, 0), (+2, 0)],
        [(-1, 0), ( 0, 0), ( 0, 0), ( 0,+1), ( 0,-2)],
        [(-1,+1), (+1,+1), (-2,+1), (+1, 0), (-2, 0)],
        [( 0,+1), ( 0,+1), ( 0,+1), ( 0,-1), ( 0,+2)],
    ]
    
    combo_table = [0, 1, 1, 2, 2, 3, 3, 4]
    
    def __init__(self, screen):
        self.clock = pygame.time.Clock()
        self.used_held = False
        self.last_move = None
        self.last_kick = None
        self.b2b = False
        self.combo = -1
        self.score = 0
        self.figure = None
        self.held = None
        self.shadow = None
        self.field = deque()
        self.state = "start"
        self.head, self.tail = self.seven_bag()
        self.remaining_time = 120000
        self.counter = 0
        self.screen = screen
        self.screen_size = screen.get_size()
        
        self.start_time = {
            pygame.K_DOWN: pygame.time.get_ticks(),
            pygame.K_LEFT: pygame.time.get_ticks(),
            pygame.K_RIGHT: pygame.time.get_ticks()
        }

        self.pressing = {
            pygame.K_DOWN: False,
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False
        }
        self.running = True
        
        for i in range(self.height):
            new_line = []
            for j in range(self.width):
                new_line.append(0)
            self.field.append(new_line)
    
    def new_figure(self, type):
        self.figure = Tetromino(type)
        # self.shadow = Tetromino(type, True)
        
    def intersects(self, shadow=False):
        item = self.shadow if shadow else self.figure
        for i in range(4):
            for j in range(4):
                if i * 4 + j in item.image():
                    if i + item.y > self.height - 1:
                        return True
                    if j + item.x > self.width - 1 or j + item.x < 0:
                        return True
                    if self.field[i + item.y][j + item.x] != 0:
                        return True
        return False

    def clear(self):
        cleared = []
        # check which lines are cleared
        for line in range(self.height - 1, -1, -1):
            for j in range(self.width):
                if self.field[line][j] == 0:
                    break
                elif j == self.width - 1:
                    cleared.append(line)
        # update 
        for line in cleared:
            del self.field[line]
        for i in range(len(cleared)):
            self.field.appendleft([0 for j in range(self.width)])
        return len(cleared)
            
    def calc_score(self, cleared_lines, check_list):
        T_spin = False
        mini = False
        if self.last_move == 'r' and len(check_list) != 0:
            if check_list[0] != 0 and check_list[1] != 0:
                T_spin = True
            elif check_list[0] != 0 or check_list[1] != 0:
                count = 0
                for mino in check_list[2:]:
                    if mino != 0:
                        count += 1
                if count == 2:
                    T_spin = True
                    mini = True
                if self.last_kick == 4:
                    mini = False
                    
        # Tetris
        if cleared_lines == 4:
            if self.b2b:
                self.score += self.score_table["b2b Tetris"]
            else:
                self.score += self.score_table["Tetris"]
        elif cleared_lines == 3:
            if T_spin:
                if self.b2b:
                    self.score += self.score_table["b2b TST"]
                else:
                    self.score += self.score_table["TST"]
            else:
                self.score += self.score_table["Triple"]
        elif cleared_lines == 2:
            if T_spin:
                if self.b2b:
                    self.score += self.score_table["b2b TSD"]
                else:
                    self.score += self.score_table["TSD"]
            else:
                self.score += self.score_table["Double"]
        elif cleared_lines == 1:
            if T_spin:
                if mini:
                    if self.b2b:
                        self.score += self.score_table["b2b TSM"]
                    else:
                        self.score += self.score_table["TSM"]
                else:
                    if self.b2b:
                        self.score += self.score_table["b2b TSS"]
                    else:
                        self.score += self.score_table["TSS"]
                        
        if cleared_lines == 4 or T_spin:
            self.b2b = True
        else:
            self.b2b = False
                    
        if self.combo >= len(self.combo_table):
            self.score += self.combo_table[-1]
        elif self.combo != -1:
            self.score += self.combo_table[self.combo]
            
        perfect = True
        for i in range(self.height):
            for j in range(self.width):
                if self.field[i][j] != 0:
                    perfect = False
                    break
        if perfect:
            self.score += 10
        
    def freeze(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    if i + self.figure.y < 2:
                        self.state = "gameover"
                    self.field[i + self.figure.y][j + self.figure.x] = self.figure.type
        
        def calc_loc_val(y, x):
            if x >= self.width or x < 0:
                return 1
            elif y >= self.height:
                return 1
            else:
                return self.field[y][x]
            
        check_list = []
        if self.figure.type == TetroType.T:
            front_pos = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]
            back_pos = [(2, 2), (2, 0), (0, 0), (0, 2), (2, 2)]
            for pos_list in [front_pos, back_pos]:
                for i in range(2):
                    check_list.append(calc_loc_val(self.figure.y + pos_list[self.figure.rotation + i][0], self.figure.x + pos_list[self.figure.rotation + i][1]))
                
        cleared_lines = self.clear()
        if cleared_lines == 0:
            self.combo = -1
        else:
            self.combo += 1
            self.calc_score(cleared_lines, check_list)
        
        self.used_held = False
        self.figure = None
    
    def hard_drop(self):
        if self.figure.y < 0:
            self.figure.y = 0
        while not self.intersects():
            self.figure.y += 1
        self.figure.y -= 1
        self.freeze()
        
    def down(self):
        prev_move = self.last_move
        self.last_move = 'd'
        self.figure.y += 1
        if self.intersects():
            self.figure.y -= 1
            self.last_move = prev_move
        
    def move(self, dir):
        if self.figure:
            temp = self.figure.x
            add = 1 if dir == "right" else -1
            self.figure.x += add
            if self.intersects():
                self.figure.x = temp
        self.update_shadow()
        self.last_move = 'm'
    
    def kick(self, ori, new, type):
        table = self.I_wall_kick if type == TetroType.I else self.wall_kick
        check_list = []
        for i in range(5):
            check_list.append(tuple((table[ori][i][0] - table[new][i][0],
                                    table[new][i][1] - table[ori][i][1])))
        original_pos = (self.figure.x, self.figure.y)
        for i, pos in enumerate(check_list):
            self.figure.x += pos[0]
            self.figure.y += pos[1]
            if self.intersects():
                self.figure.x, self.figure.y = original_pos
                continue
            else:
                self.last_kick = i
                return True
        return False
            
    def rotate(self, type):
        original_rotate = deepcopy(self.figure.rotation)
        self.figure.rotate(type)
        new_rotate = deepcopy(self.figure.rotation)
        if not self.kick(original_rotate, new_rotate, type):
            self.figure.rotate(type * -1)
        self.update_shadow()
        self.last_move = 'r'
        
    def make_shadow(self):
        self.shadow = deepcopy(self.figure)
        if self.shadow.y < 0:
            self.shadow.y = 0
        self.shadow.color = GRAY
        self.shadow.is_shadow = True
        
    def update_shadow(self):
        self.make_shadow()
        while not self.intersects(shadow=True):
            self.shadow.y += 1
        self.shadow.y -= 1

    def hold(self):
        temp = Tetromino(self.figure.type)
        self.figure = self.held
        self.held = temp
        if self.figure:
            self.update_shadow()
        self.last_move = None
        
    def seven_bag(self):
        bag = [
            TetroType.I,
            TetroType.J, 
            TetroType.L, 
            TetroType.O, 
            TetroType.S, 
            TetroType.Z, 
            TetroType.T, 
        ]
        random.shuffle(bag)
        new_figures = [Tetromino(shape) for shape in bag]
        for i in range(6):
            new_figures[i].next = new_figures[i + 1]
        return new_figures[0], new_figures[6]
        
    def update_tetro(self):
        if not self.head:
            self.head, self.tail = self.seven_bag()

        if self.figure is None and self.state not in ['gameover', 'timeup']:
            self.figure = self.head
            self.head = self.head.next
            self.update_shadow()
            
    def game_step(self):
        
        self.counter += 1
        if self.counter % (self.fps/10)  == 0:
            if self.state == "start":
                self.down()
            
        keys = pygame.key.get_pressed()
    
        for key in [pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
            if keys[key]:
                current_time = pygame.time.get_ticks()
                if current_time - self.start_time[key] > self.PRESSING_BOUND:
                    self.pressing[key] = True
            else:
                self.start_time[key] = pygame.time.get_ticks()
            
        if self.pressing[pygame.K_DOWN]:
            self.down()
        if self.pressing[pygame.K_LEFT]:
            self.move('left')
        if self.pressing[pygame.K_RIGHT]:
            self.move('right')            
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == 'gameover':
                    if event.key == pygame.K_ESCAPE:
                        self.__init__(self.screen)
                else:
                    if event.key == pygame.K_UP:
                        self.rotate(1)
                    if event.key == pygame.K_RCTRL:
                        self.rotate(-1)
                    if event.key == pygame.K_SPACE:
                        self.hard_drop()
                    if event.key == pygame.K_DOWN:
                        self.down()
                    if event.key == pygame.K_LEFT:
                        self.move("Left")
                    if event.key == pygame.K_RIGHT:
                        self.move("right")
                    if event.key == pygame.K_RSHIFT:
                        if not self.used_held:
                            self.hold()
                            self.used_held = True
                    if event.key == pygame.K_ESCAPE:
                        self.__init__(self.screen)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    self.pressing[pygame.K_DOWN] = False
                elif event.key == pygame.K_LEFT:
                    self.pressing[pygame.K_LEFT] = False
                elif event.key == pygame.K_RIGHT:
                    self.pressing[pygame.K_RIGHT] = False
                    
        if self.state not in ["gameover", "timeup"]:
            self.remaining_time -= self.clock.tick(self.fps)
        if self.remaining_time <= 0:
            self.state = "timeup"
                    
    def draw_grid(self):
        for i in range(2, self.height):
            for j in range(self.width):
                if self.field[i][j] != 0:
                    pygame.draw.rect(self.screen, Tetromino.colors[self.field[i][j]],
                                    [self.x + self.zoom * j + 1, self.y + self.zoom * i + 1, self.zoom - 2, self.zoom - 2])                
                pygame.draw.rect(self.screen, GRAY, [self.x + self.zoom * j, self.y + self.zoom * i, self.zoom, self.zoom], 1)

    def draw_tetro(self, tetro, x, y, grid: bool, size):
        for i in range(4):
            for j in range(4):
                p = i * 4 + j
                if p in tetro.image():
                    if size == self.next_zoom or (i + tetro.y >= 2 and self.state not in  ["gameover", "timeup"]):
                        pygame.draw.rect(self.screen, tetro.color,
                                        [x + size * j, y + size * i, size - 1, size - 1])
                        if grid:
                            pygame.draw.rect(self.screen, BLACK,
                                            [x + size * j, y + size * i, size, size], 1)
        
    def draw_small_grid(self, type):
        start_grid_x = self.x - self.next_zoom * 6 if type == 'h' else self.x + self.zoom * self.width
        start_grid_y = self.y + self.zoom * 2
        grid_num = 1 if type == 'h' else 5
        temp = self.held if type == 'h' else self.head
        
        
        for n in range(grid_num):
            pygame.draw.rect(self.screen, GRAY,
                        [start_grid_x, start_grid_y + self.next_zoom * 6 * n, self.next_zoom * 6, self.next_zoom * 6], 1)
            if type == 'h' and not self.held:
                break
            x_edge = 1.5
            y_edge = 2
            if temp.type == TetroType.I:
                x_edge = 1
                y_edge = 1.5
            elif temp.type == TetroType.O:
                x_edge = 1
            
            start_tetro_x = start_grid_x + self.next_zoom * x_edge
            start_tetro_y = start_grid_y + self.next_zoom * 6 * n + self.next_zoom * y_edge
            self.draw_tetro(temp, start_tetro_x, start_tetro_y, True, self.next_zoom)
            temp = temp.next
            
            if type == 'n' and not temp:
                new_head, new_tail = self.seven_bag()
                self.tail.next = new_head
                self.tail = new_tail
                temp = new_head
        
    def update_text(self):
        font = pygame.font.SysFont('Calibri', 25, True, False)
        text = font.render("Score: " + str(self.score), True, BLACK)
        
        minutes, seconds = (self.remaining_time / 1000) / 60, (self.remaining_time / 1000) % 60
        text_time = font.render("{:02d}:{:02d}".format(int(minutes), int(seconds)), True, BLACK)
        text_time_rect = text_time.get_rect()
        text_time_rect.centerx = self.screen_size[0] / 2
        
        font_over = pygame.font.SysFont('Calibri', 65, True, False)
        text_game_over = font_over.render("Game Over", True, BLACK)

        self.screen.blit(text, [10, 0])
        self.screen.blit(text_time, text_time_rect)
        
        if self.state in ["gameover", "timeup"]:
            for i in range(4):
                for j in range(4):
                    if i * 4 + j in self.figure.image():
                        self.field[i + self.figure.y][j + self.figure.x] = self.figure.type
                        self.field[i + self.shadow.y][j + self.shadow.x] = TetroType.SHADOW
                        
            finish_text = text_game_over if self.state == "gameover" else text
            self.finish(finish_text, self.screen_size)
        pygame.display.flip()
        
    def update_ui(self):
        self.screen.fill(WHITE)
        for item in [self.shadow, self.figure]:           
            if item is not None:
                self.draw_tetro(item, self.x + self.zoom * item.x + 1, self.y + self.zoom * item.y + 1, False, self.zoom)          
        self.draw_grid()
        self.draw_small_grid('h')
        self.draw_small_grid('n')
        self.update_text()
        
    def finish(self, text, pos):
        overlay = pygame.Surface(self.screen_size)
        overlay.fill((255, 255, 255))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        text_rect = text.get_rect()
        text_rect.center = (pos[0] / 2, pos[1] / 2)
        self.screen.blit(text, text_rect)

def main():
    pygame.init()
    screen_size = (400, 500)
    screen = pygame.display.set_mode(screen_size)
    game = Tetris(screen)
    game.update_ui()
    while game.running:
        game.update_tetro()
        game.game_step()
        game.update_ui()
    pygame.quit()

if __name__ == '__main__':
    main()