# Python Voxel Engine (Minecraft Clone) 

A high-performance, voxel-based sandbox game (Minecraft clone) written entirely in Python. This project leverages the power of **ModernGL** for fast GPU rendering and **Numba** for just-in-time (JIT) compilation to handle complex terrain generation efficiently.

## 🌟 Features 

* **Procedural Terrain Generation:** Utilizes Perlin noise to generate diverse landscapes including islands, hills, and cave systems.
* **Dynamic Biomes/Layers:** Terrain changes based on elevation, featuring Sand, Grass, Dirt, Stone, and Snow layers.
* **Procedural Trees:** Automatic placement of trees with wood trunks and leaves during world generation.
* **Advanced Player Physics:** 
  * Full collision detection with voxel environment.
  * Features walking, sprinting, jumping, sneaking (prevents falling off edges), and a toggleable flying mode.
  * Smooth camera transitions (e.g., FOV zoom, sneaking offset).
* **Voxel Interaction:** Ray-casting implementation allows players to accurately target, break, and place blocks in the world.
* **Chunk-based Architecture:** The world is divided into manageable chunks for efficient mesh building and rendering.
* **Optimized Rendering:** Uses `moderngl` with texture arrays and custom GLSL shaders for chunks, water, clouds, and block highlighting.
* **Interactive Hotbar:** Scroll or use number keys to select different block types to place.
* **Background Music:** Integrated ambient soundtrack using `pygame.mixer`.

## 🛠️ Technology Stack

* **[Pygame](https://www.pygame.org/):** Handles window creation, event management (mouse/keyboard), and audio.
* **[ModernGL](https://moderngl.readthedocs.io/):** Pythonic wrapper over OpenGL Core for high-performance graphics rendering.
* **[PyGLM](https://pypi.org/project/PyGLM/):** Fast mathematics library for vector and matrix operations, crucial for 3D camera and shader calculations.
* **[Numba](https://numba.pydata.org/):** JIT compiler that translates Python functions into optimized machine code, significantly speeding up procedural terrain generation loops.
* **[NumPy](https://numpy.org/):** Used for efficient multi-dimensional array operations to store voxel data.
* **[Noise](https://pypi.org/project/noise/):** Generates Perlin noise for natural-looking terrain features.

## 📂 Project Structure

```text
Minecraft/
├── main.py               # Main application loop and engine initialization
├── settings.py           # Global constants (world size, physics, colors, etc.)
├── player.py             # Player physics, input handling, and movement logic
├── camera.py             # 3D Camera, view/projection matrices, and frustum
├── world.py              # Manages the global voxel map and chunk instances
├── voxel_handler.py      # Ray casting logic for adding and removing voxels
├── terrain_gen.py        # Numba-optimized procedural terrain and tree generation
├── textures.py           # Texture loading and ModernGL texture array setup
├── shader_program.py     # GLSL shader program compilation and uniform management
├── scene.py              # Scene orchestration (world + environment features)
├── hotbar.py             # UI hotbar rendering and block selection logic
├── shaders/              # Directory containing GLSL vertex and fragment shaders
├── world_objects/        # Contains modular objects like Chunk, Water, Clouds
├── meshes/               # Mesh building logic (culling unseen voxel faces)
└── assets/               # Texture files, fonts, and background music
```

## 🎮 Controls

* **W, A, S, D:** Move forward, left, backward, right
* **Mouse:** Look around
* **Spacebar:** Jump (Double-tap Spacebar to toggle Fly Mode)
* **Left Shift:** Sneak / Descend (in Fly Mode)
* **Left Ctrl:** Sprint / Fast Fly
* **C:** Zoom camera (FOV transition)
* **Left Click:** Break block
* **Right Click:** Place block
* **1-9 or Scroll Wheel:** Select block type from the hotbar
* **Escape:** Quit the game

## 🚀 Installation & Setup

1. **Clone or Download the Repository**

2. **Install Dependencies:**
   Make sure you have Python 3 installed. Run the following command to install the required packages:
   ```bash
   pip install pygame moderngl PyGLM numba numpy noise
   ```

3. **Run the Game:**
   Execute `main.py` to start the engine:
   ```bash
   python main.py
   ```

## ⚙️ Configuration

You can tweak the game's behavior by modifying `settings.py`. Some interesting values to play with:
* `SEED`: Change the world generation seed.
* `WORLD_W`, `WORLD_H`, `WORLD_D`: Alter the dimensions of the generated world.
* `CHUNK_SIZE`: Modify the size of individual chunks.
* `FOV_DEG`: Adjust the default Field of View.
* Physics settings like `GRAVITY`, `JUMP_SPEED`, or `PLAYER_SPEED`.

## 📜 License
This project is open-source. Feel free to modify, distribute, and use it as a learning resource for building voxel engines in Python!
