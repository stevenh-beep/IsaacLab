Yes. And I recommend we **do not connect GR00T yet**.

For your first two checkpoints, the goal is simply:

```text
CHECKPOINT A
DGX Spark
   ↓
Isaac Sim
   ↓
Isaac Lab
   ↓
empty 3D window
   ↓
PASS


CHECKPOINT B
Isaac Lab
   ↓
simulated robot
   ↓
read robot state
   ↓
send a simple command
   ↓
robot moves
   ↓
PASS
```

Then, only after these work, we connect the **DROID GR00T policy**.

This is important because otherwise you'll be debugging **Isaac Sim + Isaac Lab + robot + GR00T + DROID + action conversion** simultaneously.

The current Isaac Lab documentation specifically supports DGX Spark/aarch64 with CUDA 13+, Python 3.12, and Isaac Sim 6.0.1. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/setup/installation/index.html?utm_source=chatgpt.com))

---



# Checkpoint A — Install Isaac Lab and get an empty 3D world



## A0 — What we are installing

Think of the stack like this:

```text
┌─────────────────────────────┐
│         Your Python code    │
├─────────────────────────────┤
│          Isaac Lab          │
│   robotics/simulation API   │
├─────────────────────────────┤
│          Isaac Sim          │
│  physics + rendering + USD  │
├─────────────────────────────┤
│       NVIDIA GPU / CUDA     │
├─────────────────────────────┤
│          DGX Spark          │
└─────────────────────────────┘
```

**Isaac Sim** is the simulator.

**Isaac Lab** is the robotics framework sitting on top of it.

For now, **GR00T is completely out of the picture**.

---



# A1 — Check your DGX Spark

Open a terminal.

Run:

```bash
nvidia-smi
```

You should see your NVIDIA GPU and driver information.

Then:

```bash
python3 --version
```

And:

```bash
uname -m
```

You should get:

```text
aarch64
```

because DGX Spark is ARM64/aarch64.

Also check CUDA:

```bash
nvcc --version
```

If `nvcc` isn't installed, that's not necessarily a problem. More important is that the NVIDIA driver is working.

You can also run:

```bash
nvidia-smi
```

and check that the GPU is visible.

---



# A2 — Install the DGX Spark system dependencies

The current Isaac Lab documentation specifically lists these prerequisites for DGX Spark:

```bash
sudo apt update

sudo apt install -y \
    python3.12-dev \
    libgl1-mesa-dev \
    libx11-dev \
    libxcursor-dev \
    libxi-dev \
    libxinerama-dev \
    libxrandr-dev

sudo apt install -y \
    libgl1-mesa-dev \
    libx11-dev \
    libxcursor-dev \
    libxi-dev \
    libxinerama-dev \
    libxrandr-dev
```

These are system libraries needed by the Isaac Sim graphical stack. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/setup/installation/index.html?utm_source=chatgpt.com))

Don't worry about understanding each package yet.

---



# A3 — Create a clean Conda environment

Since you already use Conda, let's keep Isaac Lab isolated.

I'd use:

```bash
conda create -n isaaclab python=3.12 -y
```

Then:

```bash
conda activate isaaclab
```

Verify:

```bash
python --version
```

You should see something like:

```text
Python 3.12.x
```



### Important

Do **not** install Isaac Lab into your existing GR00T environment.

Keep:

```text
groot environment
```

and

```text
isaaclab environment
```

separate for now.

Later we can determine whether you want one combined environment.

---



# A4 — Install Isaac Sim

The current Isaac Lab installation documentation specifies Isaac Sim:

```text
6.0.1.0
```

for the current supported workflow. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/setup/installation/index.html?utm_source=chatgpt.com))

Inside the new environment:

```bash
conda activate isaaclab
```

then:

```bash
pip install uv
```

Now install Isaac Sim:

```bash
uv pip install \
    "isaacsim[all,extscache]==6.0.1.0" \
    --extra-index-url https://pypi.nvidia.com \
    --index-strategy unsafe-best-match \
    --prerelease=allow
```

This may take a while because Isaac Sim is large.

**Don't start changing things if it looks like it's taking a long time.**

---



# A5 — Install the DGX Spark PyTorch build

Because you're on aarch64/DGX Spark, the current documentation specifies the CUDA 13 build:

```bash
uv pip install -U \
    torch==2.11.0 \
    torchvision==0.26.0 \
    --index-url https://download.pytorch.org/whl/cu130
```

This is specifically the aarch64/CUDA 13 installation path documented for DGX Spark. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/setup/installation/index.html?utm_source=chatgpt.com))

Then test:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

You want something approximately like:

```text
2.11.0
True
NVIDIA GB10
```

The exact GPU name may differ slightly.

### Very important checkpoint

If:

```text
torch.cuda.is_available()
```

returns:

```text
False
```

**stop here.**

Don't continue to Isaac Lab until CUDA/PyTorch works.

---



# A6 — Clone Isaac Lab

Create a workspace.

For example:

```bash
mkdir -p ~/groot-poc
cd ~/groot-poc
```

Clone:

```bash
git clone https://github.com/isaac-sim/IsaacLab.git
```

Enter it:

```bash
cd IsaacLab
```

You'll now have:

```text
~/groot-poc/
└── IsaacLab/
```

---



# A7 — Install Isaac Lab

Run:

```bash
./isaaclab.sh --install
```

Let it finish.

Then verify that the script exists:

```bash
ls -l isaaclab.sh
```

You should see the file.

---



# A8 — First Isaac Lab test: empty world

This is our **real Checkpoint A**.

Run:

```bash
./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py
```

The current official tutorial uses exactly this `create_empty.py` example to launch an empty Isaac Sim scene from Isaac Lab. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/00_sim/create_empty.html?utm_source=chatgpt.com))

You should eventually get an Isaac Sim window.

Conceptually:

```text
┌─────────────────────────────────────────────┐
│                                             │
│                                             │
│                 EMPTY WORLD                 │
│                                             │
│              3D viewport                    │
│                                             │
│                                             │
└─────────────────────────────────────────────┘
```

There isn't supposed to be a robot yet.

That's **correct**.

---



# A9 — What that Python script is actually doing

Open:

```bash
less scripts/tutorials/00_sim/create_empty.py
```

The important part is approximately:

```python
from isaaclab.app import AppLauncher

...

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app
```

This launches Isaac Sim.

Then:

```python
from isaaclab.sim import SimulationCfg, SimulationContext

sim_cfg = SimulationCfg(dt=0.01)
sim = SimulationContext(sim_cfg)
```

This creates the simulation.

Then:

```python
sim.reset()
```

initializes it.

And:

```python
while simulation_app.is_running():
    sim.step()
```

keeps the physics simulation running. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/00_sim/create_empty.html?utm_source=chatgpt.com))

So the mental model is:

```text
AppLauncher
     ↓
start Isaac Sim

SimulationContext
     ↓
create simulation

sim.reset()
     ↓
initialize physics

sim.step()
     ↓
advance simulation
```

That's basically all we need to understand right now.

---



# A10 — Verify that Checkpoint A passed

You have successfully completed Checkpoint A if:

### Terminal

No fatal errors.

### GPU

```bash
nvidia-smi
```

shows the Isaac Sim process using the GPU.

### GUI

An Isaac Sim window opens and displays a 3D scene.

### Python

This works:

```bash
./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py --viz kit
```

If all four are true:

# ✅ CHECKPOINT A PASSED

Don't move on until this works.

---



# Checkpoint B — Put a robot into Isaac Lab

Now things get interesting.

We're going to learn:

```text
robot
  ↓
joints
  ↓
joint positions
  ↓
joint commands
  ↓
movement
```

But **still no GR00T**.

---



# B1 — First robot: use Isaac Lab's simple Cartpole

Don't immediately try to import a DROID robot.

That's unnecessary complexity.

Isaac Lab already has a very simple articulated robot called **Cartpole**.

It's basically:

```text
          |
          |
          |
          |
       ───●───
          │
       [cart]
```

It has a cart and a pole connected by a joint.

This is useful because we can learn how Isaac Lab controls an articulated robot without dealing with a 7-DOF arm.

The official Isaac Lab articulation tutorial uses this example and demonstrates reading joint state and applying commands. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/main/source/tutorials/01_assets/run_articulation.html?utm_source=chatgpt.com))

---



# B2 — Run the official robot example

From:

```bash
cd ~/groot-poc/IsaacLab
```

run:

```bash
./isaaclab.sh -p scripts/tutorials/01_assets/run_articulation.py --viz kit
```

You should get a simulation containing cartpole robots that move.

The official tutorial uses this command and demonstrates setting joint state and commands. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/01_assets/run_articulation.html?utm_source=chatgpt.com))

You should see something like:

```text
        |
        |
        |
        |
        ●
     ┌─────┐
     │cart │
     └─────┘
```

and it will move.

---



# B3 — What is an "articulation"?

You'll see this word constantly in Isaac Lab.

For now, just translate:

> **articulation = a robot made of connected rigid pieces and joints**

For example:

```text
shoulder
   │
   ●  ← joint
   │
 upper arm
   │
   ●  ← joint
   │
 forearm
   │
   ●  ← joint
   │
 gripper
```

A robotic arm is therefore an articulation.

Cartpole is an extremely simple articulation:

```text
cart
 │
 ● joint
 │
pole
```

---



# B4 — Understand the robot's state

This is where we start building the foundation for GR00T.

A robot has a **state**.

For the moment, imagine:

```python
joint_position
joint_velocity
```

For a simple robot:

```text
joint_position = 0.35
joint_velocity = 0.02
```

For a 7-joint arm, it might be:

```text
joint_position =
[
    0.12,
   -0.43,
    1.02,
    0.77,
   -0.31,
    0.52,
    0.10
]
```

Those numbers describe the current configuration of the robot.

---



# B5 — Understand the action

An **action** is what we ask the robot to do.

For example:

```text
current joint position:

[0.10, 0.20, 0.30]

desired:

[0.20, 0.20, 0.30]
```

We're telling the simulator:

> Move joint 1 toward 0.20.

This is very different from your CCTV/VLM work.

Your current VLM pipeline is approximately:

```text
image
  ↓
VLM
  ↓
JSON
```

VLA is:

```text
image
+
robot state
+
language
      ↓
    GR00T
      ↓
   action
      ↓
robot
      ↓
new image/state
```

That's the concept we're slowly building toward.

---



# B6 — Look at the official articulation code

Open:

```bash
less scripts/tutorials/01_assets/run_articulation.py
```

Look for:

```python
robot.data.joint_pos
```

That gives you the simulated robot's joint positions.

You'll also see code that writes joint state into the simulator and applies commands.

The official tutorial explains the basic loop as:

```text
set joint target
       ↓
write data to simulator
       ↓
physics step
       ↓
update robot state
       ↓
read new state
```

([Isaac Sim](https://isaac-sim.github.io/IsaacLab/main/source/tutorials/01_assets/run_articulation.html?utm_source=chatgpt.com))

That loop is **extremely important** for your eventual GR00T integration.

---



# B7 — Your first "robot control loop"

Conceptually, what Isaac Lab is doing is:

```python
while simulation_running:

    # 1. Read robot
    state = robot.data.joint_pos

    # 2. Decide what to do
    action = ...

    # 3. Send command
    robot.set_joint_position_target(action)

    # 4. Apply command
    robot.write_data_to_sim()

    # 5. Advance physics
    sim.step()

    # 6. Update state
    robot.update(...)
```

Don't worry if the exact API names aren't familiar yet.

The important thing is the **loop**.

---



# B8 — First manual/programmatic control experiment

Once the official Cartpole example works, create your own copy.

```bash
cp \
    scripts/tutorials/01_assets/run_articulation.py \
    playground_scripts/run_articulation_my_first_robot.py
```

Now:

```bash
nano my_first_robot.py
```

We're going to make **one tiny change at a time**.

Find the section where the example applies its random effort/action.

The official tutorial currently does something conceptually like:

```python
efforts = torch.randn_like(robot.data.joint_pos) * 5.0

robot.set_joint_effort_target(efforts)
robot.write_data_to_sim()
```

([Isaac Sim](https://isaac-sim.github.io/IsaacLab/main/source/tutorials/01_assets/run_articulation.html?utm_source=chatgpt.com))

Instead of random movement, we want a predictable command.

For example:

```python
efforts = torch.zeros_like(robot.data.joint_pos)
efforts[:, 0] = 2.0

robot.set_joint_effort_target(efforts)
robot.write_data_to_sim()
```

Now we're saying:

```text
joint 0
  ↓
apply +2 effort
```

rather than:

```text
random effort
```

---



# B9 — Run your modified program

From the Isaac Lab directory:

```bash
./isaaclab.sh -p playground_scripts/run_articulation_my_first_robot.py  --viz kit
```

Now the robot should behave predictably instead of randomly.

If it moves:

# ✅ CHECKPOINT B PASSED

You have now established:

```text
Python
  ↓
Isaac Lab
  ↓
Isaac Sim
  ↓
Physics
  ↓
Robot
  ↓
joint command
  ↓
robot moves
```

---



# B10 — The important thing we have NOT done yet

We have **not** used GR00T.

That's deliberate.

We currently have:

```text
              Isaac Lab
                  │
                  ▼
             simulated robot
                  │
          ┌───────┴───────┐
          ▼               ▼
       state            action
          │               │
          └───────┬───────┘
                  ▼
               physics
                  │
                  ▼
            new robot state
```

Eventually we'll replace the manually generated `action` with:

```text
                 camera
                   +
                language
                   +
              robot state
                   │
                   ▼
            GR00T N1.7
                   │
                   ▼
              DROID action
                   │
                   ▼
          simulated robot
```

---



# But there is one important DROID issue

You specifically asked to use **DROID**.

That's good, but we shouldn't pretend that the Cartpole is a DROID robot.

The DROID GR00T embodiment expects:

```text
2 camera images

exterior_image_1_left
wrist_image_left
```

plus:

```text
eef_9d
gripper_position
joint_position
```

which totals:

```text
9 + 1 + 7 = 17 state dimensions
```

and produces the corresponding **17-dimensional action representation**. ([GitHub](https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com))

So our eventual pipeline needs something more like:

```text
                  Isaac Lab
                     │
             simulated DROID-like arm
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
   camera 1      camera 2       robot state
       │             │             │
       └─────────────┼─────────────┘
                     ▼
                GR00T N1.7
                     │
                     ▼
             17-D DROID action
                     │
                     ▼
               robot controller
                     │
                     ▼
             simulated robot
```

And **that is the next stage**, not Checkpoint B.

The base N1.7 model officially supports DROID inference zero-shot with:

```text
OXE_DROID_RELATIVE_EEF_RELATIVE_JOINT
```

and NVIDIA provides a DROID demo dataset specifically for this. ([GitHub](https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com))

---



# Your immediate roadmap

I recommend we proceed exactly in this order:

```text
                    YOU ARE HERE
                         │
                         ▼
┌─────────────────────────────────────────────┐
│ A. Isaac Lab installation                   │
│                                             │
│ DGX Spark                                  │
│    ↓                                        │
│ Isaac Sim 6.0.1                             │
│    ↓                                        │
│ Isaac Lab                                   │
│    ↓                                        │
│ empty 3D world                              │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ B. Robot basics                             │
│                                             │
│ Cartpole                                    │
│    ↓                                        │
│ read joint state                            │
│    ↓                                        │
│ send joint command                          │
│    ↓                                        │
│ robot moves                                  │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ C. Real robotic arm in simulation           │
│                                             │
│ 7-DOF arm                                   │
│    ↓                                        │
│ joints + gripper                            │
│    ↓                                        │
│ camera                                      │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ D. DROID observation format                 │
│                                             │
│ camera × 2                                  │
│ +                                           │
│ 17-D state                                  │
│ +                                           │
│ language                                    │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ E. GR00T N1.7 DROID inference               │
│                                             │
│ observations                                │
│      ↓                                      │
│ GR00T                                       │
│      ↓                                      │
│ 17-D action chunk                            │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ F. Execute GR00T actions in Isaac Lab       │
│                                             │
│ GR00T action                                 │
│      ↓                                      │
│ simulated robot                              │
│      ↓                                      │
│ new state + images                           │
│      ↓                                      │
│ GR00T again                                  │
└─────────────────────────────────────────────┘
```

**For now, stop after A and B.** Don't install additional robot assets or start modifying GR00T yet.

The official Isaac Lab tutorials themselves recommend progressing from creating an empty scene into interacting with assets/articulations, which is exactly the separation above. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/index.html?utm_source=chatgpt.com))

### Official references

- [Isaac Lab — Installation](https://isaac-sim.github.io/IsaacLab/develop/source/setup/installation/index.html?utm_source=chatgpt.com)
- [Isaac Lab — Creating an empty scene](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/00_sim/create_empty.html?utm_source=chatgpt.com)
- [Isaac Lab — Interacting with an articulation](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/01_assets/run_articulation.html?utm_source=chatgpt.com)
- [GR00T — DROID example](https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com)

