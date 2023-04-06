import torch
import torch.nn as nn
from tetris_ai import game_init, post_move, info

class Your_Model(nn.Module):
    def __init__(self):
        super().__init__()
        
    def forward(self):
        pass
    
model = Your_Model()

def fit(game_thread, model):
    game = info.get()
    while game_thread.is_alive() and game.running:
        action = model(game.get_state())
        post_move(action)
            

if __name__ == "__main__":
    game_init(fit, model)