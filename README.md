# 🌌 Nokia Snake Game — Galaxy Edition 🐍

An immersive, retro-futuristic **Nokia Snake Game** engineered in Python using **Pygame-CE**, **OpenCV**, and the **MediaPipe Tasks API**. 

Experience the classic nostalgic feel of the legendary Nokia 3310 Snake game combined with a stunning **deep-space Galaxy Theme**, AI-powered hand gesture controls, custom sound effects, and smooth multi-stage menu navigation!

---

## 🌟 Game UI, Audio & Features

* **Stunning Galaxy Edition UI**:
  * Features a gorgeous deep-space starfield background with twinkling stars and animated floating space characters.
  * Sleek modern typography paired with vibrant neon cyan (`#00E5FF`) and magenta (`#FF0080`) glowing accents.
* **Immersive Sound Effects (SFX)**:
  * **App Startup**: Nostalgic opening jingle as you enter the cosmic universe.
  * **UI Clicks**: Crisp audio feedback whenever you press buttons, select speeds, or navigate menus.
  * **Gameplay Audio**: Satisfying munching sound effects when the snake feeds on cosmic energy.
  * **Game Over**: Distinct sound effect signaling a collision accompanied by your final score breakdown.
* **Multi-Stage Navigation Flow**:
  1. **Main Menu**: Choose between starting the game, viewing the rules, or reading about the game's engineering.
  2. **Speed Selection**: Pick your challenge level (**Easy**, **Intermediate**, or **Fast**) before diving into action.
  3. **How to Play & About**: Interactive info screens outlining gesture controls and background history.

---

## 🕹️ Controls & Gestures Summary

You can play seamlessly using either AI web-camera hand gestures or traditional keyboard/mouse controls!

| Action | Primary AI Gesture Control | Alternative Keyboard / Mouse Control |
| :--- | :--- | :--- |
| **Change Direction** | Point **Index Finger** (Up ▲, Down ▼, Left ◄, Right ►) | **Arrow Keys** or Click On-Screen UI Buttons |
| **Restart Game** | Show **Peace Sign (✌️)** during Game Over | Press **`R`** key on Keyboard |
| **Exit Game** | Close Window (`X` button) | Close Window (`X` button) |

---

## 🚀 Quick Start & Installation Guide

Follow these step-by-step instructions to set up your environment, install dependencies, and run the application on your desktop inside VS Code.

### Step 1: Clone the Repository (For new users downloading from GitHub)
If you are downloading or cloning the repository to your machine, open your terminal and run:
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
cd YOUR_REPOSITORY_NAME

### Step 2: Create & Activate a Virtual Environment
It is strongly recommended to use a virtual environment to manage dependencies cleanly.

For Windows (PowerShell / VS Code Terminal):

Powershell
python -m venv .venv
.\.venv\Scripts\Activate
For macOS / Linux (Terminal):

Bash
python -m venv .venv
source .venv/bin/activate

###Step 3: Install Dependencies
With your virtual environment active, install all required packages using the provided requirements file:

Bash
pip install -r requirements.txt


###Step 4: Download the MediaPipe Hand Tracker Asset File
The app requires the pre-trained Google MediaPipe hand_landmarker.task model file in your root folder for webcam hand gesture tracking.

For Windows (PowerShell):

PowerShell
Invoke-WebRequest -Uri "[https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)" -OutFile "hand_landmarker.task"

For macOS / Linux (Terminal):

Bash
curl -L -o hand_landmarker.task [https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)


###Step 5: Run the Application
Launch the game by executing the main script:

Bash
python main.py
