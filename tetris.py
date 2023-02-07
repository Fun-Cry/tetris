import pygame
from collections import deque
import random
from copy import deepcopy
from enum import Enum
import numpy as np

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

class control(Enum):
    RIGHT_ROTATE = 1
    LEFT_ROTATE = 2
    LEFT = 3
    RIGHT = 4
    HARD = 5
    DOWN = 6
    HOLD = 7
    RESTART = 8
    
    LONG_LEFT = 9
    LONG_RIGHT = 10
    SOFT_DROP = 11
    DROP_RIGHT = 12
    DROP_LEFT = 13
    

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
    
    type2idx = {
        TetroType.I : 1,
        TetroType.J : 2,
        TetroType.L : 3,
        TetroType.O : 4,
        TetroType.S : 5,
        TetroType.Z : 6,
        TetroType.T : 7,
    }
    
    left_most_x = {
        TetroType.I : [0, 2, 0, 1],
        TetroType.O : [1],
        TetroType.S : [0, 1, 0, 0],
    }

    width = {
        TetroType.I : [4, 1, 4, 1],
        TetroType.O : [2],
        TetroType.S : [3, 2, 3, 2],
    }
    
    def __init__(self, type_, is_shadow=False):
        self.type_ = type_
        self.is_shadow = is_shadow
        self.color = GRAY if is_shadow else self.colors[self.type_] 
        self.rotation = 0
        self.x = 3
        self.y = 0
        self.cur_x = 3
        self.max_x = 9
        self.next = None
        self.update_cur_max()
    
    def image(self):
        return self.rotations[self.type_][self.rotation]
    
    def rotate(self, rotation_type):
        self.rotation = (self.rotation + rotation_type) % len(self.rotations[self.type_])
        self.update_cur_max()
        
    def update_cur_max(self):
        type_ = self.type_ if self.type_ in [TetroType.I, TetroType.O] else TetroType.S
        self.cur_x =  self.x + self.left_most_x[type_][self.rotation]
        self.max_x = 10 - self.width[type_][self.rotation]

            
class Tetris:
    height = 22
    width = 10
    x = 100
    y = 20
    zoom = 20
    next_zoom = zoom / 2
    PRESSING_BOUND = 300
    fps = 10000
    screen_size = (400, 500)
    move_keys = {
        control.RIGHT_ROTATE: pygame.K_UP,
        control.LEFT_ROTATE: pygame.K_RCTRL,
        control.LEFT: pygame.K_LEFT,
        control.RIGHT: pygame.K_RIGHT,
        control.HARD: pygame.K_SPACE,
        control.DOWN: pygame.K_DOWN,
        control.HOLD: pygame.K_RSHIFT,
        control.RESTART: pygame.K_ESCAPE
    }
    
    score_table = {
        'Double' : 1,
        'Triple' : 2,
        'Tetris' : 4,
        'TSM' : 1,
        'TSS' : 2,
        'TSD' : 4,
        'TST' : 6,
        'b2b Tetris' : 6,
        'b2b TSM' : 2,
        'b2b TSS' : 3,
        'b2b TSD' : 6,
        'b2b TST' : 9,
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
    
    def __init__(self, display=True):
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
        self.state = 'start'
        self.head, self.tail = self._seven_bag()
        self.remaining_time = 120000
        self.counter = 0
        self.screen = None
        self.display = display
        
        if self.display:
            self.screen = pygame.display.set_mode(self.screen_size)
            
        self.start_time = {
            self.move_keys[control.DOWN]: pygame.time.get_ticks(),
            self.move_keys[control.LEFT]: pygame.time.get_ticks(),
            self.move_keys[control.RIGHT]: pygame.time.get_ticks()
        }

        self.pressing = {
            self.move_keys[control.DOWN]: False,
            self.move_keys[control.LEFT]: False,
            self.move_keys[control.RIGHT]: False
        }
        self.running = True
        
        for i in range(self.height):
            new_line = []
            for j in range(self.width):
                new_line.append(0)
            self.field.append(new_line)
        
    def _intersects(self, shadow=False):
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

    def _clear(self):
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
            
    def _calc_score(self, cleared_lines, check_list):
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
                    
        if cleared_lines == 4:
            if self.b2b:
                self.score += self.score_table['b2b Tetris']
            else:
                self.score += self.score_table['Tetris']
        elif cleared_lines == 3:
            if T_spin:
                if self.b2b:
                    self.score += self.score_table['b2b TST']
                else:
                    self.score += self.score_table['TST']
            else:
                self.score += self.score_table['Triple']
        elif cleared_lines == 2:
            if T_spin:
                if self.b2b:
                    self.score += self.score_table['b2b TSD']
                else:
                    self.score += self.score_table['TSD']
            else:
                self.score += self.score_table['Double']
        elif cleared_lines == 1:
            if T_spin:
                if mini:
                    if self.b2b:
                        self.score += self.score_table['b2b TSM']
                    else:
                        self.score += self.score_table['TSM']
                else:
                    if self.b2b:
                        self.score += self.score_table['b2b TSS']
                    else:
                        self.score += self.score_table['TSS']
                        
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
        
    def _freeze(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    if i + self.figure.y < 2:
                        self.state = 'gameover'
                    self.field[i + self.figure.y][j + self.figure.x] = self.figure.type_
                    
        for key in self.pressing:
            self.pressing[key] = False
            
        for key in self.start_time:
            self.start_time[key] = pygame.time.get_ticks()
        
        def calc_loc_val(y, x):
            if x >= self.width or x < 0:
                return 1
            elif y >= self.height:
                return 1
            else:
                return self.field[y][x]
            
        check_list = []
        if self.figure.type_ == TetroType.T:
            front_pos = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]
            back_pos = [(2, 2), (2, 0), (0, 0), (0, 2), (2, 2)]
            for pos_list in [front_pos, back_pos]:
                for i in range(2):
                    check_list.append(calc_loc_val(self.figure.y + pos_list[self.figure.rotation + i][0], self.figure.x + pos_list[self.figure.rotation + i][1]))
                
        cleared_lines = self._clear()
        if cleared_lines == 0:
            self.combo = -1
        else:
            self.combo += 1
            self._calc_score(cleared_lines, check_list)
        
        self.used_held = False
        self.figure = None
    
    def _hard_drop(self):
        if self.figure.y < 0:
            self.figure.y = 0
        while not self._intersects():
            self.figure.y += 1
        self.figure.y -= 1
        self._freeze()
        
    def _down(self):
        prev_move = self.last_move
        self.last_move = 'd'
        self.figure.y += 1
        if self._intersects():
            self.figure.y -= 1
            self.last_move = prev_move
        
    def _move(self, dir):
        if self.figure:
            temp = self.figure.x
            add = 1 if dir == 'right' else -1
            self.figure.x += add
            self.figure.update_cur_max()
            if self._intersects():
                self.figure.x = temp
        self._update_shadow()
        self.last_move = 'm'
    
    def _kick(self, ori, new, type_):
        table = self.I_wall_kick if type_ == TetroType.I else self.wall_kick
        check_list = []
        for i in range(5):
            check_list.append(tuple((table[ori][i][0] - table[new][i][0],
                                    table[new][i][1] - table[ori][i][1])))
        original_pos = (self.figure.x, self.figure.y)
        for i, pos in enumerate(check_list):
            self.figure.x += pos[0]
            self.figure.y += pos[1]
            if self._intersects():
                self.figure.x, self.figure.y = original_pos
                continue
            else:
                self.last_kick = i
                return True
        return False
            
    def _rotate(self, type_: int):
        original_rotate = deepcopy(self.figure.rotation)
        self.figure.rotate(type_)
        new_rotate = deepcopy(self.figure.rotation)
        if not self._kick(original_rotate, new_rotate, type_):
            self.figure.rotate(type_ * -1)
        self._update_shadow()
        self.last_move = 'r'
        
    def _make_shadow(self):
        self.shadow = deepcopy(self.figure)
        if self.shadow.y < 0:
            self.shadow.y = 0
        self.shadow.color = GRAY
        self.shadow.is_shadow = True
        
    def _update_shadow(self):
        self._make_shadow()
        while not self._intersects(shadow=True):
            self.shadow.y += 1
        self.shadow.y -= 1

    def _hold(self):
        temp = Tetromino(self.figure.type_)
        self.figure = self.held
        self.held = temp
        if self.figure:
            self._update_shadow()
        self.last_move = None
        
    def _seven_bag(self):
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
        
    def _update_tetro(self):
        if not self.head:
            self.head, self.tail = self._seven_bag()

        if self.figure is None and self.state not in ['gameover', 'timeup']:
            self.figure = self.head
            self.head = self.head.next
            self._update_shadow()
          
    def _update_counter(self):
        
        self.counter += 1
        if self.counter % (self.fps/10)  == 0:
            if self.state == 'start':
                self._down()
                
        if self.state not in ['gameover', 'timeup']:
            self.remaining_time -= self.clock.tick(self.fps)
        if self.remaining_time <= 0:
            self.state = 'timeup'
          
            
    def step(self):
        self._update_tetro()
        self._update_counter()
        keys = pygame.key.get_pressed() 
    
        for key in self.start_time.keys():
            if keys[key]:
                current_time = pygame.time.get_ticks()
                if self.start_time and current_time - self.start_time[key] > self.PRESSING_BOUND:
                    self.pressing[key] = True
            
        if self.pressing[self.move_keys[control.DOWN]]:
            self._down()
        if self.pressing[self.move_keys[control.LEFT]]:
            self._move('left')
        if self.pressing[self.move_keys[control.RIGHT]]:
            self._move('right')            
            
        for event in pygame.event.get():
            current_time = pygame.time.get_ticks()
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state in ['gameover', 'timeup'] :
                    if event.key == self.move_keys[control.RESTART]:
                        self.__init__(self.display)
                else:
                    if event.key == self.move_keys[control.RIGHT_ROTATE]:
                        self._rotate(1)
                    if event.key == self.move_keys[control.LEFT_ROTATE]:
                        self._rotate(-1)
                    if event.key == self.move_keys[control.HARD]:
                        self._hard_drop()
                    if event.key == self.move_keys[control.DOWN]:
                        self._down()
                        self.start_time[event.key] = current_time
                    if event.key == self.move_keys[control.LEFT]:
                        self._move('Left')
                        self.start_time[event.key] = current_time
                    if event.key == self.move_keys[control.RIGHT]:
                        self._move('right')
                        self.start_time[event.key] = current_time
                    if event.key == self.move_keys[control.HOLD]:
                        if not self.used_held:
                            self._hold()
                            self.used_held = True
                    if event.key == self.move_keys[control.RESTART]:
                        self.__init__(self.display)
            elif event.type == pygame.KEYUP:
                for key in self.pressing.keys():
                    if event.key == key:
                        self.pressing[key] = False
                        self.start_time[key] = None
                        
        if self.display:
            self._update_ui()
            
        return pygame.time.get_ticks()
                
    def _draw_grid(self):
        for i in range(2, self.height):
            for j in range(self.width):
                if self.field[i][j] != 0:
                    pygame.draw.rect(self.screen, Tetromino.colors[self.field[i][j]],
                                    [self.x + self.zoom * j + 1, self.y + self.zoom * i + 1, self.zoom - 2, self.zoom - 2])                
                pygame.draw.rect(self.screen, GRAY, [self.x + self.zoom * j, self.y + self.zoom * i, self.zoom, self.zoom], 1)

    def _draw_tetro(self, tetro, x, y, grid: bool, size):
        for i in range(4):
            for j in range(4):
                p = i * 4 + j
                if p in tetro.image():
                    if size == self.next_zoom or (i + tetro.y >= 2 and self.state not in  ['gameover', 'timeup']):
                        pygame.draw.rect(self.screen, tetro.color,
                                        [x + size * j, y + size * i, size - 1, size - 1])
                        if grid:
                            pygame.draw.rect(self.screen, BLACK,
                                            [x + size * j, y + size * i, size, size], 1)
        
    def _draw_small_grid(self, type_):
        start_grid_x = self.x - self.next_zoom * 6 if type_ == 'h' else self.x + self.zoom * self.width
        start_grid_y = self.y + self.zoom * 2
        grid_num = 1 if type_ == 'h' else 5
        temp = self.held if type_ == 'h' else self.head
        
        for n in range(grid_num):
            pygame.draw.rect(self.screen, GRAY,
                        [start_grid_x, start_grid_y + self.next_zoom * 6 * n, self.next_zoom * 6, self.next_zoom * 6], 1)
            if type_ == 'h' and not self.held:
                break
            x_edge = 1.5
            y_edge = 2
            if temp.type_ == TetroType.I:
                x_edge = 1
                y_edge = 1.5
            elif temp.type_ == TetroType.O:
                x_edge = 1
            
            start_tetro_x = start_grid_x + self.next_zoom * x_edge
            start_tetro_y = start_grid_y + self.next_zoom * 6 * n + self.next_zoom * y_edge
            self._draw_tetro(temp, start_tetro_x, start_tetro_y, True, self.next_zoom)
            temp = temp.next
            
            if type_ == 'n' and not temp:
                new_head, new_tail = self._seven_bag()
                self.tail.next = new_head
                self.tail = new_tail
                temp = new_head
        
    def _update_text(self):
        font = pygame.font.SysFont('Calibri', 25, True, False)
        text = font.render('Score: ' + str(self.score), True, BLACK)
        
        minutes, seconds = (self.remaining_time / 1000) / 60, (self.remaining_time / 1000) % 60
        text_time = font.render('{:02d}:{:02d}'.format(int(minutes), int(seconds)), True, BLACK)
        text_time_rect = text_time.get_rect()
        text_time_rect.centerx = self.screen_size[0] / 2
        
        font_over = pygame.font.SysFont('Calibri', 65, True, False)
        text_game_over = font_over.render('Game Over', True, BLACK)

        self.screen.blit(text, [10, 0])
        self.screen.blit(text_time, text_time_rect)
        
        if self.state in ['gameover', 'timeup']:
            if self.figure:
                for i in range(4):
                    for j in range(4):
                        if i * 4 + j in self.figure.image():
                            self.field[i + self.figure.y][j + self.figure.x] = self.figure.type_
                            self.field[i + self.shadow.y][j + self.shadow.x] = TetroType.SHADOW
                        
            finish_text = text_game_over if self.state == 'gameover' else text
            self.finish(finish_text, self.screen_size)
        pygame.display.flip()
        
    def _update_ui(self):
        self.screen.fill(WHITE)
        for item in [self.shadow, self.figure]:           
            if item is not None:
                self._draw_tetro(item, self.x + self.zoom * item.x + 1, self.y + self.zoom * item.y + 1, False, self.zoom)          
        self._draw_grid()
        self._draw_small_grid('h')
        self._draw_small_grid('n')
        self._update_text()
        
    def finish(self, text, pos):
        overlay = pygame.Surface(self.screen_size)
        overlay.fill((255, 255, 255))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        text_rect = text.get_rect()
        text_rect.center = (pos[0] / 2, pos[1] / 2)
        self.screen.blit(text, text_rect)
        
    def get_state(self):
        while not self.figure:
            self.step()
        
        cur_held_next = []
        cur_held_next.append(Tetromino.type2idx[self.figure.type_])
        if not self.held:
            cur_held_next.append(0)
        else:
            cur_held_next.append(Tetromino.type2idx[self.held.type_])
        
        next_ = self.head
        for i in range(5):
            cur_held_next.append(Tetromino.type2idx[next_.type_])
            next_ = next_.next
        cur_held_next = np.array(cur_held_next)
        
        grid_info = []
        for row in self.field:
            temp = [0 if mino == 0 else 1 for mino in row]
            grid_info.append(temp)
        board = np.array(grid_info)
        
        return board, cur_held_next

class Tetris_AI:
    def __init__(self, game: Tetris):
        self.game = game
        self.event_queue = []
        self.move_per_sec = 0.01
    
    def _place_one_tetro(self, moves=list[control]):
        start_time = self.game.step()
        end_time = start_time
        move_mapping = {
            control.LONG_LEFT: control.LEFT,
            control.LONG_RIGHT: control.RIGHT,
            control.SOFT_DROP: control.DOWN,
        }
        for move in moves:
            if move in [control.LONG_LEFT, control.LONG_RIGHT]:
                key_ = self.game.move_keys[move_mapping[move]]
                while end_time - start_time < self.game.PRESSING_BOUND:
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key_))
                    end_time = self.game.step()
                pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key_))
            elif move == control.SOFT_DROP:
                prev_y = -1
                while self.game.figure.y != prev_y:
                    prev_y = self.game.figure.y
                    key_ = self.game.move_keys[move_mapping[move]]
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key_))
                    end_time = self.game.step()
            else:
                key_ = self.game.move_keys[move]
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key_))
                pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key_))
                
            while self.game.step() - end_time < (1 / self.move_per_sec):
                continue
        return self.game.step()
                    
    def play(self):
        
        if len(self.event_queue) == 0:
            self.game.step()
            return
        
        for place_move in self.event_queue:
            end_time = self._place_one_tetro(place_move)
        
        while self.game.step() - end_time < (1 / self.move_per_sec):
            continue
            
        self.event_queue = []
    
    def move(self, rotation, x: int, down: control, dm: control, turn: int):
        while not self.game.figure:
            self.game.step()
        
        f_copy = deepcopy(self.game.figure)
        for i in range(rotation):
            f_copy.rotate(1)
            
        place_tetro_move = []
        cur_x = f_copy.cur_x
        max_x = f_copy.max_x
        x = min(x, max_x)
        
        if rotation == 4:
            place_tetro_move = [control.HOLD]
            self.event_queue.append(place_tetro_move)
            return
        
        if rotation == 0:
            place_tetro_move += []
        elif rotation == 1:
            place_tetro_move += [control.RIGHT_ROTATE]
        elif rotation == 2:
            place_tetro_move += [control.RIGHT_ROTATE for i in range(2)]
        elif rotation == 3:
            place_tetro_move += [control.LEFT_ROTATE]
        
        # left and right
        if x == 0:
            place_tetro_move += [control.LONG_LEFT]
        elif x == max_x:
            place_tetro_move += [control.LONG_RIGHT]
        elif x == 1:
            place_tetro_move += [control.LONG_LEFT, control.RIGHT]
        elif x == max_x - 1:
            place_tetro_move += [control.LONG_RIGHT, control.LEFT]
        else:
            distance = x - cur_x
            if distance < 0:
                move = control.LEFT
                distance *= -1
            else:
                move = control.RIGHT
            place_tetro_move += [move for i in range(distance)]
        
        
        # drop
        if down == control.HARD:
            place_tetro_move += [control.HARD]
            self.event_queue.append(place_tetro_move)
            return
        else:
            place_tetro_move += [control.SOFT_DROP]
            
        place_tetro_move += [dm]
            
        if down == control.DROP_RIGHT:
            place_tetro_move += [control.RIGHT_ROTATE for i in range(turn)]
        elif down == control.DROP_LEFT:
            place_tetro_move += [control.LEFT_ROTATE for i in range(turn)]

        place_tetro_move += [control.HARD]
        self.event_queue.append(place_tetro_move)
    
def main():
    pygame.init()
    game = Tetris()
    while game.running:
        game.step()
    pygame.quit()

if __name__ == '__main__':
    main()