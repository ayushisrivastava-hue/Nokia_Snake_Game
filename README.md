# Nokia Snake Game — Galaxy Edition 🐍🌌

A NOKIA inspired Snake game built with Python. It pairs a galaxy themed interface and generated sound effects with optional webcam hand gesture controls, while keeping keyboard and on screen controls available too.

## Features

- Galaxy themed animated menus and game screen
- Easy, Intermediate, and Fast difficulty levels
- Webcam gesture steering with a keyboard and on screen button fallback
- Rules and About screens
- Procedurally generated startup, click, food, and game over sounds
- Score tracking and restart after a game ends

## Tech stack

| Technology | Role |
| --- | --- |
| Python | Application language and game logic |
| Pygame-CE | Window, rendering, input, and game audio |
| OpenCV | Webcam capture and camera frame handling |
| MediaPipe Tasks | Hand landmark detection for gesture input |
| NumPy | Image and audio sample arrays |

The game is organized across `main.py` (menus, rendering, and app loop), `snake_engine.py` (Snake rules and scoring), `gesture_detector.py` (hand landmark interpretation), and `sound_effects.py` (generated audio). The MediaPipe hand landmark model is `hand_landmarker.task` in the project root.

## User workflow

1. Start the app to reach the main menu. Choose **Start Game**, **How to Play**, or **About** with the mouse or keyboard.
2. Choose **Easy**, **Intermediate**, or **Fast** on the start screen, then begin. The webcam gesture worker starts when gameplay begins.
3. Steer by pointing your index finger in the direction you want the snake to move. If the camera is unavailable, use the arrow keys or the on screen direction buttons.
4. Eat food to grow and increase your score. Avoid running into the walls or the snake's body.
5. After a collision, press **R** to restart OR SHOW PEACE SIGN . Close the game window to exit.

## Controls

| Action | Control |
| --- | --- |
| Navigate menus | Mouse or keyboard arrows; press Enter to select |
| Change direction | Point with index finger, use keyboard arrow keys, or click an on screen direction button |
| Restart after game over | `R` |
| Exit | Close the window |

## Setup and run

### Requirements

- Python 3.9 or newer
- A webcam for gesture controls (optional; keyboard and on screen controls work without it)
- `hand_landmarker.task` in the project root for gesture detection

### 1. Get the project

```bash
git clone <repository-url>
cd NokiaSnakeGesture
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Get the hand landmark model

If `hand_landmarker.task` is not already present in the project root, download it:

```bash
python -c "from urllib.request import urlretrieve; urlretrieve('https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task', 'hand_landmarker.task')"
```

### 5. Launch the game

```bash
python main.py
```

## Project files

```text
main.py                 Menus, visuals, input, and application loop
snake_engine.py         Snake movement, food, collision, and scoring
gesture_detector.py     Webcam hand landmark and gesture processing
sound_effects.py        Procedurally generated game sound effects
requirements.txt        Python package dependencies
hand_landmarker.task    MediaPipe hand landmark model
```
