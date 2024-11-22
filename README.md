# Swap'em!

A colorful match-three puzzle game built with Python and Pygame. An experiment to see how well the lightweight Claude 3.5 Haiku model can perform in coding tasks. Rather well, it seems. IMHO as of November 2024 it surpasses OpenAI's GPT4o. :) This one took about 120 minutes of back-and-forth with the LLM, easily my easiest co-coding sessions with an AI so far.

![image](https://github.com/user-attachments/assets/ade99087-e443-4f20-96d0-fab80dd6a6a1)

## Description

Swap'em! is a classic match-three puzzle game where players swap adjacent tiles to create matches of three or more tiles of the same color. The game features:

- Four difficulty levels (5-8 colors)
- Beautiful gradient tiles with hover effects
- Chain reaction scoring system
- High score tracking for each difficulty level, stored locally in a JSON file
- Smooth animations for tile swapping and matching

## Requirements

- Python 3.x
- Pygame

## Installation

1. Clone this repository:
```bash
git clone https://github.com/jussinrepo/swap-em.git
```

2. Install the required dependency:
```bash
pip install pygame
```

3. Run the game:
```bash
python swap-em.py
```

## How to Play

1. Start by selecting your difficulty level (5-8 colors)
2. Click on a tile to select it
3. Click on an adjacent tile to swap them
4. Create matches of three or more tiles of the same color
5. Chain reactions will give you bonus points
6. Game ends when no more valid moves are available

## Controls

- **Mouse**: Select and swap tiles
- **ESC**: Return to main menu / Exit game
- **Click**: Start new game from game over screen

## Scoring

- 3 tiles: 30 points × chain multiplier
- 4 tiles: 50 points × chain multiplier
- 5 tiles: 100 points × chain multiplier
- 6+ tiles: 200 points × chain multiplier

Chain multiplier increases with consecutive matches in a single move.

## Features

- Individual high score tracking for each difficulty level
- Gradient tile graphics with hover highlighting
- Smooth animations for tile swapping and matching
- Chain reaction bonus scoring system
- Game tips displayed on game over screen

## License

MIT

## Credits

Created by Jussi Sivonen
