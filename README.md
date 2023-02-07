# Tetris

A simple tetris game that aims to restore the classic Tetris Friends gameplay

![](screenshot.png)

## Installation and Running

1. Install the environment:

```bash
conda env create -f environment.yaml
conda activate tetris
```

2. Run `tetris.py`

```bash
python tetris.py
```

## Gameplay

The game is controlled using the following keyboard controls:

- **Move left**: Left arrow key
- **Move right**: Right arrow key
- **Move down**: Down arrow key
- **Rotate clockwise**: Up arrow key
- **Rotate counterclockwise**: Right Ctrl key
- **Hold**: Right Shift key

## Machine Playable Interface

Play tetris with external programs using tetris_ai.py

1. Run `python tetris_ai.py`

2. Append input to `movements.txt`

### Input Format

Each line in `movements.txt` should consist of 5 variables, `R`, `X`, `D`, `M`, `T`, separated by space.

- `R`: Rotation. Specifies the orientation for the Tetrimino, with values in the range of \[0, 3\].
- `X`: Horizontal placement. Determines where the current tetrimino should go, with values in the range of \[0, 9\].
- `D`: Down. Describes how to place the current tetrimino.
  - **0**: Hard Drop. If this is specified, m and t have no effect on the movement.
  - **1**: Soft Drop.
  - **2**: Soft Drop + Left Rotation. Used in T-spin and other wall kick scenarios.
  - **3**: Soft Drop + Right Rotation.
- `M`: Movements after Soft Drop.
  - **0**: The current Tetrimino moves to the left-most position after Soft Drop.
  - **1**: The current Tetrimino moves to the right-most position after Soft Drop.
  - **2**: The current Tetrimino stays at **x**
- `T`: Rotations after Soft Drop. Specifies how many rotations to perform.

Example: `3 5 3 0 2`

- The Tetrimino does a **left rotation**, moves to the **5th position**, performs **Soft Drop**, moves to the **left-most** position and then does **two right rotations**.

## Reference

- **Fundamental structure**: https://levelup.gitconnected.com/writing-tetris-in-python-2a16bddb5318
- **Rules**: https://tetris.fandom.com/wiki/Tetris_Friends
