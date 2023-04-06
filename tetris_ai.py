import threading
from tetris import Tetris, Tetris_AI, control
import pygame
import queue

drop_mapping = {
    0: control.HARD,
    1: control.SOFT_DROP,
    2: control.DROP_LEFT,
    3: control.DROP_RIGHT,
}
move_mapping = {
    0: control.LONG_LEFT,
    1: control.LONG_RIGHT,
    2: None
}

q = queue.Queue()
info = queue.Queue()

def run_game():
    pygame.init()
    game = Tetris()
    player = Tetris_AI(game)
    
    info.put(game)
    
    while game.running:
        if not q.empty():
            r, x, d, m, t = q.get()
            d = drop_mapping[d]
            m = move_mapping[m]
            player.move(r, x, d, m, t)
        player.play()
    pygame.quit()
    
def post_move(move):
    q.put(move)
    

def handle_input(target):
    while target.is_alive():
        move = map(int, input().split())
        post_move(move)
        
def game_init(input_source, *args):
    game_thread = threading.Thread(target=run_game)
    game_thread.start()
    
    input_thread = threading.Thread(target=input_source, args=[game_thread, *args])
    input_thread.start()
    
    game_thread.join()
    input_thread.join()
    
if __name__ == '__main__':
    game_init(handle_input)