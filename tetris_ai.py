from tetris import Tetris, Tetris_AI, control
import pygame
import time
pygame.init()

game = Tetris()
player = Tetris_AI(game)

position = 0
cur = 0

drop_mapping = {
    0: control.HARD,
    1: control.SOFT_DROP,
    2: control.DROP_LEFT,
    3: control.DROP_RIGHT,
}
move_mapping = {
    0: control.LONG_LEFT,
    1: control.LONG_RIGHT,
}
while game.running:
    contents = ''
    with open('movement.txt', 'r', encoding='utf-8') as f:
        f.seek(position)
        contents = f.read()
        position = f.tell()

    try:
        r, x, d, m, t = [int(_) for _ in contents.split()]
        d = drop_mapping[d]
        m = move_mapping[m]
        player.move(r, x, d, m, t)
    except:
        pass
    
    player.play()
    cur += 1
    
with open('movement.txt', 'w', encoding='utf-8') as f:
    f.write('')
pygame.quit()