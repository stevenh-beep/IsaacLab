Yes. Since you have already successfully run **GR00T N1.7 inference**, I would now separate the problem into two very clear pieces:

> **GR00T = brain**
> **Isaac Lab = simulated robot + physics + camera**

The goal of this stage is **not** to build a complete robot-learning system yet. It is simply:

```text
GR00T
  │
  │ predicts actions
  ▼
Isaac Lab simulated robot
  │
  │ applies actions
  ▼
robot moves on screen
```

There is one important caveat: **the DROID demo you just used is not automatically an Isaac Lab robot simulation**. The standalone script performs open-loop inference on DROID trajectories and compares predicted actions with ground truth. NVIDIA's current GR00T code does provide a `Gr00tSimPolicyWrapper`, but that's an interface layer for simulation environments; it does not mean the DROID MP4s themselves magically become a simulated robot. ([GitHub][1])

So I recommend we build this in **two stages**:

1. **Isaac Lab installation + make sure a robot visibly moves**
2. **Connect GR00T to that simulation**

Do **not** try to solve both at once.

---

# Stage 1 — Understand what Isaac Lab actually is

Since you're completely new to robotics, this distinction is important.

You currently have:

```text
DROID dataset
     │
     ├── camera image
     ├── robot state
     ├── language
     └── ground-truth action
             │
             ▼
          GR00T
             │
             ▼
       predicted action
```

Isaac Lab adds a simulated physical world:

```text
                    Isaac Lab
               ┌─────────────────┐
               │                 │
               │   simulated     │
               │     robot       │
               │       │         │
camera ───────►│       ▼         │
               │   robot state   │
               │       │         │
               │       ▼         │
               │    physics      │
               │       │         │
               └───────┼─────────┘
                       │
                       ▼
                    GR00T
                       │
                  action chunk
                       │
                       ▼
                simulated robot
```

The **action** is simply a command to the robot.

For example, conceptually:

```text
move joint 1 slightly
move joint 2 slightly
move joint 3 slightly
open gripper
```

The actual DROID representation is more complicated, and **we should not guess its dimensions or meaning**. GR00T's embodiment configuration defines the action representation. ([GitHub][2])

---

# Stage 2 — Don't create another Python environment yet

This is important for your machine.

You already have your GR00T environment working.

I recommend keeping:

```text
GR00T environment
       +
Isaac Lab environment
```

separate initially.

Why?

Because you're going to be debugging two large systems:

* GR00T / PyTorch / Transformers
* Isaac Sim / Isaac Lab / rendering / physics

If we put everything into one environment immediately, a dependency problem becomes much harder to understand.

Current Isaac Lab documentation explicitly supports **DGX Spark**, including CUDA 13+ and Python 3.12. The current documentation also gives a Conda-based installation path. ([Isaac Sim][3])

---

# Stage 3 — Install Isaac Lab

First check your OS and architecture:

```bash
uname -m
```

On DGX Spark you should get:

```text
aarch64
```

Then:

```bash
nvidia-smi
```

and:

```bash
python3 --version
```

We want Python 3.12 for the Isaac Lab environment.

---

## 3.1 Install system dependencies

Isaac Lab's current DGX Spark instructions require these development packages:

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
```

This comes directly from the current Isaac Lab installation documentation for DGX Spark/aarch64. ([Isaac Sim][3])

---

# Stage 4 — Create a separate Conda environment

You prefer Conda, so let's use it.

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

You want:

```text
Python 3.12.x
```

---

# Stage 5 — Install Isaac Sim

This is the slightly confusing part.

**Isaac Lab is not the actual 3D simulator.**

Think of it as:

```text
Isaac Sim
   │
   ├── physics
   ├── rendering
   ├── simulated cameras
   ├── robot models
   └── 3D world
          ▲
          │
       Isaac Lab
          │
          ├── robot-learning environments
          ├── tasks
          ├── observations
          └── actions
```

The current Isaac Lab documentation uses Isaac Sim 6.0.1.0 for this installation path. ([Isaac Sim][3])

Install it with:

```bash
uv pip install \
    "isaacsim[all,extscache]==6.0.1.0" \
    --extra-index-url https://pypi.nvidia.com \
    --index-strategy unsafe-best-match \
    --prerelease=allow
```

Because you're on DGX Spark/aarch64, install the CUDA 13 PyTorch build:

```bash
uv pip install -U \
    torch==2.11.0 \
    torchvision==0.26.0 \
    --index-url https://download.pytorch.org/whl/cu130
```

Those are the current DGX Spark installation instructions from Isaac Lab. ([Isaac Sim][3])

---

# Stage 6 — Get Isaac Lab

Clone it somewhere separate from GR00T.

For example:

```bash
cd ~/groot-poc

git clone https://github.com/isaac-sim/IsaacLab.git

cd IsaacLab
```

Then install Isaac Lab:

```bash
./isaaclab.sh --install
```

At this point your directory should conceptually look like:

```text
~/groot-poc/
│
├── Isaac-GR00T/
│
├── IsaacLab/
│
└── inspect/
```

---

# Stage 7 — First test: DON'T involve GR00T

This is extremely important.

Before we connect GR00T, let's prove:

> **Isaac Lab itself works on your DGX Spark.**

Run:

```bash
cd ~/groot-poc/IsaacLab

./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py
```

You should eventually get an Isaac Sim window.

You may see a mostly empty 3D scene.

That's good.

At this point you have proven:

```text
DGX Spark
   ↓
Isaac Sim
   ↓
Isaac Lab
   ↓
3D rendering works
```

**Do not proceed until this works.**

---

# Stage 8 — Your first robot

Now we want an actual robot.

But don't worry about GR00T yet.

Isaac Lab contains example environments and robot assets.

Run:

```bash
./isaaclab.sh -p scripts/tutorials/01_assets/run_articulation.py
```

The exact tutorial filenames can change between Isaac Lab releases, so if that path doesn't exist, run:

```bash
find scripts -iname "*articulation*" | head -30
```

We're looking for an example that loads an **articulation**.

---

# What is an articulation?

This is one robotics term you'll encounter constantly.

A robot isn't represented as one solid object.

For example:

```text
           shoulder
              ●
              │
              │ upper arm
              │
              ● elbow
              │
              │ forearm
              │
              ● wrist
              │
           gripper
```

Each `●` is approximately a **joint**.

Isaac Sim represents the robot as a collection of connected rigid bodies and joints.

That collection is called an:

> **articulation**

So when you see:

```python
robot = Articulation(...)
```

don't overthink it.

It basically means:

> "This is the simulated robot whose joints I want to control."

---

# Stage 9 — The critical robotics concept: state → action

This is the concept I want you to understand before connecting GR00T.

Imagine the robot has six joints.

Its current state might be:

```text
state =
[
    0.20,
    0.10,
   -0.30,
    0.50,
    0.10,
    0.00
]
```

Those numbers might represent joint positions.

Then GR00T produces an action:

```text
action =
[
    +0.01,
    -0.02,
    +0.01,
     0.00,
     0.02,
    -0.01
]
```

If those are **relative joint commands**, the simulator might apply:

```text
new_state =
[
    0.21,
    0.08,
   -0.29,
    0.50,
    0.12,
   -0.01
]
```

But:

**Do not assume this is what DROID does.**

Your current embodiment tag:

```text
OXE_DROID_RELATIVE_EEF_RELATIVE_JOINT
```

is specifically telling GR00T what action representation to use.

The current GR00T policy returns decoded actions according to the model's modality configuration. ([GitHub][2])

This is why we inspected `modality.json` earlier.

---

# Stage 10 — Where GR00T enters

Now we can build the real loop.

Conceptually:

```text
                 ┌──────────────────┐
                 │    Isaac Lab     │
                 │                  │
                 │ simulated robot  │
                 │       │          │
                 │       ▼          │
                 │  robot state     │
                 │       │          │
                 │       ▼          │
                 │ simulated camera │
                 └───────┬──────────┘
                         │
                         │ observation
                         ▼
                 ┌──────────────────┐
                 │      GR00T       │
                 │                  │
                 │ image            │
                 │ state            │
                 │ language         │
                 └────────┬─────────┘
                          │
                          │ action chunk
                          ▼
                 ┌──────────────────┐
                 │    Isaac Lab     │
                 │                  │
                 │ apply actions    │
                 └────────┬─────────┘
                          │
                          ▼
                     robot moves
                          │
                          └──────────► next observation
```

That is what people mean when they say **closed-loop control**.

---

# Stage 11 — Why your current standalone script isn't enough

Your current command:

```bash
uv run python scripts/deployment/standalone_inference_script.py \
    --model-path nvidia/GR00T-N1.7-3B \
    --dataset-path demo_data/droid_sample \
    --embodiment-tag OXE_DROID_RELATIVE_EEF_RELATIVE_JOINT \
    --traj-ids 1 2 \
    --inference-mode pytorch \
    --execution-horizon 8
```

is effectively doing:

```text
DROID dataset
     │
     ├── image
     ├── state
     └── language
          │
          ▼
        GR00T
          │
          ▼
      predicted actions
          │
          ▼
    compare against GT
```

It isn't doing:

```text
Isaac Lab
    ↓
GR00T
    ↓
Isaac Lab robot
    ↓
physics
    ↓
new camera/state
    ↓
GR00T
```

The official DROID example describes this as open-loop inference and reports predicted-vs-ground-truth metrics. ([GitHub][4])

---

# Stage 12 — Use the GR00T server architecture

For the eventual integration, I recommend **not modifying the GR00T model itself**.

Instead:

```text
Isaac Lab
     │
     │ observation
     ▼
GR00T server
     │
     │ action
     ▼
Isaac Lab
```

GR00T already provides a policy server for this kind of deployment. ([GitHub][5])

Start it from your existing GR00T environment:

```bash
cd ~/groot-poc/Isaac-GR00T

conda activate groot-n17
```

Then:

```bash
uv run python gr00t/eval/run_gr00t_server.py \
    --model-path nvidia/GR00T-N1.7-3B \
    --embodiment-tag OXE_DROID_RELATIVE_EEF_RELATIVE_JOINT \
    --device cuda:0
```

You should get something conceptually like:

```text
Starting GR00T inference server...

Embodiment tag: ...
Model path: ...
Device: cuda:0
Host: 0.0.0.0
Port: 5555
```

Now GR00T is sitting there waiting for observations.

---

# Stage 13 — But don't connect Isaac Lab yet

This is where I want to deliberately slow you down.

There are **three different things** we need to match:

### 1. Observation

Isaac Lab must provide something like:

```text
image
state
language
```

### 2. Embodiment

GR00T expects a particular robot representation:

```text
DROID
```

but Isaac Lab may have:

```text
Franka
Panda
SO-101
Unitree
etc.
```

Those are **not interchangeable**.

### 3. Action

Isaac Lab might expect:

```text
joint position targets
```

while GR00T might produce:

```text
relative EEF + relative joint actions
```

So we need an adapter:

```text
GR00T action
      ↓
ACTION ADAPTER
      ↓
Isaac Lab robot command
```

This is probably the single most important robotics concept for your current project.

---

# Stage 14 — What robot should we simulate?

For **learning robotics**, I'd actually recommend a small arm rather than jumping into humanoids.

Something conceptually like:

```text
        camera
          │
          ▼

       ┌───────┐
       │       │
       │  arm  │
       │       │
       └───┬───┘
           │
         gripper
           │
      ┌────┴────┐
      │  cube   │
      └─────────┘
```

Eventually:

```text
              GR00T
                │
                ▼
       simulated SO-101
                │
                ▼
             cube
```

Then eventually:

```text
              GR00T
                │
                ▼
           physical SO-101
                │
                ▼
             cube
```

That transition is much easier to understand than starting with a humanoid.

---

# One important warning about N1.7 + Isaac Lab

I don't want to give you the misleading impression that there is currently a single official NVIDIA command like:

```bash
run_groot_isaac_lab.py
```

that takes your exact **N1.7 DROID zero-shot checkpoint** and makes a simulated robot perform the DROID task.

There are current GR00T simulation interfaces and the `Gr00tSimPolicyWrapper`, but you still have to match the simulation's observation/action interface and robot embodiment. ([GitHub][2])

In fact, there are recent discussions around N1.7 simulation setups where users are explicitly asking for official Isaac Sim reference environments for particular embodiments, so I would avoid building your learning path around an unofficial repository that happens to claim "GR00T + Isaac Lab." ([GitHub][6])

---

# Your exact roadmap from here

I recommend we do this **one checkpoint at a time**:

### Checkpoint A — Isaac Lab installation

```text
DGX Spark
   ↓
Isaac Sim
   ↓
Isaac Lab
   ↓
empty 3D world
```

### Checkpoint B — simulated robot

```text
Isaac Lab
   ↓
robot
   ↓
move robot manually/programmatically
```

### Checkpoint C — simulated camera

```text
robot
  +
camera
  ↓
RGB image
```

### Checkpoint D — inspect observation

We print:

```text
image.shape
state.shape
state values
```

and actually **display the image**.

### Checkpoint E — GR00T outside simulation

You already achieved this:

```text
DROID
 ↓
GR00T
 ↓
action
```

### Checkpoint F — connect GR00T to Isaac Lab

```text
Isaac Lab observation
        ↓
      GR00T
        ↓
     action
        ↓
  Isaac Lab robot
```

### Checkpoint G — visualize everything

This is the interface I ultimately want you to have:

```text
┌──────────────────────────────────────────────────────────┐
│                   GR00T + ISAAC LAB                     │
├─────────────────────────────┬────────────────────────────┤
│                             │ Episode: 12                │
│                             │ Step: 183                  │
│       SIMULATED CAMERA      │                            │
│                             │ Language:                  │
│          [ IMAGE ]           │ "pick up the cube"         │
│                             │                            │
│                             │ Robot state:               │
│                             │ [ ... ]                    │
│                             │                            │
│                             │ GR00T action:              │
│                             │ [ ... ]                    │
│                             │                            │
│                             │ Executed action:           │
│                             │ [ ... ]                    │
│                             │                            │
│                             │ Action horizon: 8          │
└─────────────────────────────┴────────────────────────────┘
```

And eventually record:

```text
runs/
└── 2026-09-02_1530/
    ├── camera/
    │   ├── 000000.png
    │   ├── 000001.png
    │   └── ...
    │
    ├── state/
    │   ├── 000000.npy
    │   └── ...
    │
    ├── gr00t_action/
    │   ├── 000000.npy
    │   └── ...
    │
    └── video.mp4
```

That will fit **very nicely** with the way you've been inspecting your CCTV/VLM pipelines: every timestep becomes inspectable rather than treating the VLA as a black box.

## So your immediate next action

**Don't connect GR00T yet.**

Run only these steps:

```bash
conda create -n isaaclab python=3.12 -y
conda activate isaaclab
```

then install the DGX Spark prerequisites:

```bash
sudo apt install -y \
    python3.12-dev \
    libgl1-mesa-dev \
    libx11-dev \
    libxcursor-dev \
    libxi-dev \
    libxinerama-dev \
    libxrandr-dev
```

then Isaac Sim:

```bash
uv pip install \
    "isaacsim[all,extscache]==6.0.1.0" \
    --extra-index-url https://pypi.nvidia.com \
    --index-strategy unsafe-best-match \
    --prerelease=allow
```

and CUDA-13 PyTorch:

```bash
uv pip install -U \
    torch==2.11.0 \
    torchvision==0.26.0 \
    --index-url https://download.pytorch.org/whl/cu130
```

These versions are based on the **current Isaac Lab DGX Spark installation documentation**, rather than an older GR00T tutorial. ([Isaac Sim][3])

**Then stop and test Isaac Sim/Isaac Lab.** Once you have the first 3D window working, the next step should be very concrete: **load a simple arm, make one joint move, and explain exactly what a joint, articulation, action, state, timestep, controller, and physics step are while you watch it happen.**

[1]: https://github.com/NVIDIA/Isaac-GR00T/blob/main/scripts/deployment/standalone_inference_script.py?utm_source=chatgpt.com "Isaac-GR00T/scripts/deployment/standalone_inference_script.py at main · NVIDIA/Isaac-GR00T · GitHub"
[2]: https://github.com/NVIDIA/Isaac-GR00T/blob/main/gr00t/policy/gr00t_policy.py?utm_source=chatgpt.com "Isaac-GR00T/gr00t/policy/gr00t_policy.py at main · NVIDIA/Isaac-GR00T · GitHub"
[3]: https://isaac-sim.github.io/IsaacLab/develop/source/setup/installation/index.html?utm_source=chatgpt.com "Installation — Isaac Lab Documentation"
[4]: https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com "Isaac-GR00T/examples/DROID/README.md at main · NVIDIA/Isaac-GR00T · GitHub"
[5]: https://github.com/NVIDIA/Isaac-GR00T?ref=taaft&utm_source=chatgpt.com "GitHub - NVIDIA/Isaac-GR00T at taaft · GitHub"
[6]: https://github.com/NVIDIA/Isaac-GR00T/issues/760?utm_source=chatgpt.com "[REAL_G1 / N1.7] Is there an official Isaac Sim setup and is zero-shot behavior expected? · Issue #760 · NVIDIA/Isaac-GR00T · GitHub"

