Yes. Since you already completed **Checkpoint A** and the Cartpole version of B, I would now move to a **real robotic arm + gripper**, and then add a camera and inspect exactly what Isaac Lab produces.

One important correction to the earlier roadmap: **for these checkpoints, I would use Franka Panda first, not try to force the DROID embodiment onto an Isaac Lab robot yet.** Franka is already a built-in Isaac Lab manipulation asset, has 7 arm joints + gripper, and Isaac Lab has official examples for both joint-level control and task-space control. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/?utm_source=chatgpt.com))

Then, in Checkpoint E/F, we can make the observation/action interface match **GR00T's DROID format**.

The progression becomes:

```text
A  DONE
Isaac Sim + Isaac Lab
        ↓
empty world


B  ← YOU ARE DOING NOW
Isaac Lab
   ↓
Franka Panda + gripper
   ↓
read joint state
   ↓
command joints
   ↓
robot moves


C
Franka
   +
camera
   ↓
RGB image


D
RGB image
+
robot state
   ↓
print / visualize observations


E
DROID-format observations
   +
language
   ↓
GR00T N1.7
   ↓
DROID 17-D action


F
GR00T action
   ↓
simulated robot
```

---



# Checkpoint B — Real robotic arm + gripper



## B0 — What robot are we going to use?

We're going to use **Franka Panda**.

Visually, think:

```text
                 ┌── gripper ──┐
                 │             │
                 ▼             ▼
                ═══           ═══
                   \         /
                    \_______/
                        │
                       joint
                        ●
                       /
                      /
                     ●
                    /
                   ●
                  /
                 ●
                /
               ●
              /
             ●
            /
           ●
          /
       BASE
```

It is a proper 7-DOF manipulation arm with a parallel gripper.

Isaac Lab includes Franka as one of its built-in fixed-arm robots. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/?utm_source=chatgpt.com))

---



# B1 — First, find the current Franka examples

From your Isaac Lab directory:

```bash
cd ~/groot-poc/IsaacLab
```

Search the installed examples:

```bash
find scripts -iname "*franka*" | head -50
```

Also:

```bash
find scripts -iname "*diff_ik*" -o -iname "*joint*" | head -50
```

You should find examples related to:

```text
Franka
Differential IK
joint control
```

Isaac Lab's current task-space controller tutorial explicitly supports:

```text
franka_panda
ur10
```

and uses a Franka configuration called `FRANKA_PANDA_HIGH_PD_CFG`. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/05_controllers/run_diff_ik.html?utm_source=chatgpt.com))

---



# B2 — Run the Franka differential-IK example


| Neural Network World                | Robot Arm (Differential IK) World                     |
| ----------------------------------- | ----------------------------------------------------- |
| **Loss function**                   | How far the hand is from the desired pose (the error) |
| **Gradient**                        | Jacobian                                              |
| **Optimizer / Solver** (SGD, Adam…) | Differential IK controller                            |
| **Network weights**                 | Joint angles                                          |
| **One training step**               | One small joint correction                            |
| **Many training steps**             | Hand gradually moves to the target                    |




### Why they feel so similar

In a neural network:

1. You compute the loss (how wrong the prediction is).
2. You compute the gradient (how each weight affects the loss).
3. You take a small step to reduce the loss.

In Differential IK:

1. You compute the pose error (how far the hand is from the goal).
2. You use the **Jacobian** (how each joint affects the hand pose).
3. You take a small step in joint space to reduce the error.

The Jacobian plays almost exactly the same role as the gradient.

That’s why Differential IK is sometimes called a “local linear approximation” or “gradient-based” method for solving Inverse Kinematics — it keeps making small corrective steps using local sensitivity information (the Jacobian), just like gradient descent.

Try:

```bash
./isaaclab.sh -p scripts/tutorials/05_controllers/run_diff_ik.py
```

If your checkout contains that tutorial at that path, this should open Isaac Sim with the Franka arm.

The current official tutorial creates a Franka robot and a differential inverse-kinematics controller. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/05_controllers/run_diff_ik.html?utm_source=chatgpt.com))

You should see something like:

```text
                    gripper
                   ╱      ╲
                  ╱        ╲
                 ●          ●
                  \        /
                   \______/
                       |
                       ●
                      /
                     /
                    ●
                   /
                  ●
                 /
                ●
               /
              ●
             /
            BASE
```

and the arm should move between predefined end-effector goals.

---



# B3 — What just happened?

This is actually a very important robotics concept.

The example gives the arm a target like:

```text
x = 0.5
y = 0.5
z = 0.7
```

plus orientation.

For example:

```python
ee_goal = [
    0.5,
    0.5,
    0.7,
    ...
]
```

The controller figures out:

> "What should each of my 7 joints do so that the gripper reaches that position?"

This is called **inverse kinematics (IK)**.

You don't need to master IK yet.

Just remember:

```text
task-space command
        ↓
"put gripper HERE"
        ↓
inverse kinematics
        ↓
joint commands
        ↓
robot moves
```

The official Isaac Lab example uses `DifferentialIKController` for exactly this purpose. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/05_controllers/run_diff_ik.html?utm_source=chatgpt.com))

---



# B4 — But we want to understand joint control first

Before worrying about IK, let's directly control the joints.

Find the articulation example:

```bash
find scripts/tutorials -name "run_articulation.py"
```

You already used it for Cartpole.

Open it:

```bash
nano scripts/tutorials/01_assets/run_articulation.py
```

You'll notice that the example is written around the generic `Articulation` API.

The important concept is:

```python
robot.data.joint_pos
```

That gives the current joint positions.

Isaac Lab's articulation tutorial specifically demonstrates reading joint state and applying commands to articulated robots. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/01_assets/run_articulation.html?utm_source=chatgpt.com))

---



# B5 — Find the Franka configuration

Run:

```bash
grep -R "FRANKA_PANDA" -n source/isaaclab | head -30
```

You should find something along the lines of:

```text
FRANKA_PANDA_CFG
FRANKA_PANDA_HIGH_PD_CFG
```

The exact names can change between Isaac Lab versions, so **use the configuration that exists in your checkout**, rather than blindly copying an old tutorial.

You can also search:

```bash
grep -R "FRANKA_PANDA_HIGH_PD_CFG" -n .
```

The current official IK tutorial uses:

```python
FRANKA_PANDA_HIGH_PD_CFG
```

for the Panda. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/05_controllers/run_diff_ik.html?utm_source=chatgpt.com))

---



# B6 — Understand the Franka state

Now we're getting close to the kind of data GR00T consumes.

The robot has joint positions:

```python
robot.data.joint_pos
```

For Franka you'll see approximately:

```text
[
    joint_1,
    joint_2,
    joint_3,
    joint_4,
    joint_5,
    joint_6,
    joint_7,
    finger_1,
    finger_2
]
```

So conceptually:

```text
7 arm joints
+
2 gripper joints
```

The exact tensor shape depends on how many environments and joints are instantiated.

For one robot it will be something conceptually like:

```text
(1, 9)
```

where:

```text
1 = number of simulated environments
9 = robot joints
```

---



# B7 — Make your first controlled movement

Rather than modifying the official tutorial immediately, I recommend making a copy:

```bash
cp \
scripts/tutorials/05_controllers/run_diff_ik.py \
/home/axonex/Documents/IsaacLab/playground_scripts/checkpoint_1/run_diff_ik_my_franka.py

./isaaclab.sh -p /home/axonex/Documents/IsaacLab/playground_scripts/checkpoint_1/run_diff_ik_my_franka.py --viz kit --num_envs 1
```

Then:

```bash
cd ~/groot-poc
```

and:

```bash
nano my_franka.py
```

We want eventually to replace:

```text
predefined target sequence
```

with:

```text
our own target
```

For example:

```text
start
  ↓
gripper at position A
  ↓
move to position B
  ↓
hold
  ↓
move back to A
```

---



# B8 — Don't touch the gripper yet

For the **first** experiment, just move the arm.

Why?

Because we want to isolate:

```text
ARM
```

from:

```text
GRIPPER
```

First prove:

```text
joint command
    ↓
arm moves
```

Then:

```text
gripper command
    ↓
gripper opens/closes
```

Then combine them.

---



# B9 — Test the gripper

Once the arm works, find the Franka joint names.

A very useful thing to add temporarily is:

```python
print(robot.joint_names)
```

You'll get something approximately like:

```text
[
    'panda_joint1',
    'panda_joint2',
    ...
    'panda_joint7',
    'panda_finger_joint1',
    'panda_finger_joint2'
]
```

Don't hard-code the indices until you've printed what **your installed asset** actually reports.

That's a good robotics habit:

> **Inspect the robot rather than assuming its joint ordering.**

Then you can identify:

```text
arm:
0 ... 6

gripper:
7 ... 8
```

if that's what your installed configuration reports.

---



# B10 — Your first useful robot-state print

Add something like:

```python
print("joint names:", robot.joint_names)
print("joint positions:", robot.data.joint_pos)
print("joint velocities:", robot.data.joint_vel)
```

You should see values changing while the robot moves.

Conceptually:

```text
joint positions:

[
  0.000,
 -0.785,
  0.000,
 -2.356,
  0.000,
  1.571,
  0.785,
  0.040,
  0.040
]
```

Don't worry if your actual values are different.

The important point is:

```text
robot.data.joint_pos
```

is the **simulated robot's current state**.

---



# B11 — Understand the simulation loop

At this point you should be able to visualize:

```text
                 ┌───────────────┐
                 │ Isaac Physics │
                 └───────┬───────┘
                         │
                         ▼
                  robot.data
                         │
                         ▼
                  joint positions
                         │
                         │
                    YOUR CODE
                         │
                         ▼
                  joint command
                         │
                         ▼
                 Isaac simulation
                         │
                         ▼
                   robot moves
```

And that loop repeats many times per second.

This is the fundamental interface we'll eventually use for GR00T.

---



# B12 — Checkpoint B success criteria

Don't move to the camera until all of these work:

### 1. Franka appears

```text
☑ Panda arm visible
☑ gripper visible
```



### 2. Arm moves

```text
☑ programmatically controlled
☑ not just random motion
```



### 3. You can read state

```python
robot.data.joint_pos
```



### 4. You can identify joints

```python
robot.joint_names
```



### 5. Gripper can eventually be controlled

```text
☑ open
☑ close
```

Once that's working:

# ✅ CHECKPOINT B PASSED

---



# Checkpoint C — Add a simulated camera

Now we add the other half of the eventual VLA input.

The target is:

```text
               Franka
                  │
                  │
                  ▼
              ┌───────┐
              │camera │
              └───┬───┘
                  │
                  ▼
              RGB image
```

Isaac Lab's camera system is a renderer-backed sensor. The camera can output RGB, depth, normals and other data. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/overview/core-concepts/sensors/camera.html?utm_source=chatgpt.com))

---



# C1 — Find the camera example

Run:

```bash
find scripts/tutorials -iname "*camera*" | sort
```

You should find something similar to:

```text
scripts/tutorials/04_sensors/...
```

The current Isaac Lab documentation includes a `run_usd_camera.py` tutorial specifically for using a camera sensor. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/main/source/how-to/save_camera_output.html?utm_source=chatgpt.com))

---



# C2 — Run the official camera example first

Try:

```bash
./isaaclab.sh -p \
scripts/tutorials/04_sensors/run_usd_camera.py \
--enable_cameras --viz kit
```

The current official example documents this exact GUI invocation. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/main/source/how-to/save_camera_output.html?utm_source=chatgpt.com))

You should see a scene with a camera.

At this point we are testing:

```text
Isaac Lab
   ↓
Camera
   ↓
render
   ↓
image
```

before combining it with our Franka.

---



# C3 — Understand what an RGB image actually is

This is important for your VLM background.

Isaac Lab's camera gives RGB data as:

```text
torch.uint8
```

with shape:

```text
(B, H, W, 3)
```

where:

```text
B = number of cameras/environments
H = image height
W = image width
3 = RGB
```

For example:

```text
(1, 480, 640, 3)
```

means:

```text
1 image
480 pixels high
640 pixels wide
3 channels
```

Each pixel contains:

```text
[R, G, B]
```

with values:

```text
0 ... 255
```

The current Isaac Lab camera documentation explicitly specifies this `(num_cameras, height, width, 3)` RGB format and `torch.uint8` type. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/overview/core-concepts/sensors/camera.html?utm_source=chatgpt.com))

---



# C4 — Add a camera to the Franka scene

Now we combine:

```text
Franka
+
Camera
```

Your scene should eventually look conceptually like:

```text
             CAMERA
                │
                │ sees
                ▼
       ┌─────────────────┐
       │                 │
       │     FRANKA      │
       │       ARM       │
       │        │        │
       │        ▼        │
       │     GRIPPER     │
       │                 │
       └─────────────────┘
```

The easiest way to do this is to take your working Franka script and add a `CameraCfg`.

Conceptually:

```python
from isaaclab.sensors import Camera
```

and:

```python
camera_cfg = CameraCfg(
    prim_path="{ENV_REGEX_NS}/Camera",
    height=480,
    width=640,
    data_types=["rgb"],
    ...
)
```

The exact spawn configuration should follow the camera example in your installed Isaac Lab version; the current API supports RGB through `data_types=["rgb"]`. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/overview/core-concepts/sensors/camera.html?utm_source=chatgpt.com))

---



# C5 — Position the camera

For the first experiment, **don't attach it to the robot**.

Put it somewhere like:

```text
              CAMERA
                 \
                  \
                   \
                    ▼
             ┌───────────┐
             │           │
             │  FRANKA   │
             │           │
             └───────────┘
```

That gives you a fixed "external camera".

This is actually closer to the DROID setup conceptually because DROID has an external camera plus a wrist camera. The official DROID embodiment expects:

```text
exterior_image_1_left
wrist_image_left
```

as its two visual inputs. ([GitHub](https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com))

We will eventually recreate that structure.

---



# C6 — Read the RGB image

After the simulation has rendered:

```python
camera.update(dt)
```

you can access:

```python
image = camera.data.output["rgb"]
```

The current Isaac Lab API documents exactly this pattern for camera output. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/overview/core-concepts/sensors/camera.html?utm_source=chatgpt.com))

Then:

```python
print(image.shape)
print(image.dtype)
```

You should get something like:

```text
torch.Size([1, 480, 640, 3])
torch.uint8
```

Again, your exact resolution may differ.

---



# Checkpoint C success criteria

You want:

```text
☑ Franka exists
☑ camera exists
☑ camera sees Franka
☑ RGB output exists
☑ image has shape (..., H, W, 3)
☑ dtype is uint8
```

Then:

# ✅ CHECKPOINT C PASSED

---



# Checkpoint D — Inspect the observation

Now we make this much more interesting.

We're going to create your first little **robot observation inspector**.

The target is:

```text
┌──────────────────────────────────────────────┐
│             SIMULATION OBSERVATION            │
├──────────────────────────────────────────────┤
│                                              │
│  RGB IMAGE                                   │
│                                              │
│  ┌──────────────────────────────┐            │
│  │                              │            │
│  │        FRANKA ARM            │            │
│  │                              │            │
│  │             🤖               │            │
│  │                              │            │
│  └──────────────────────────────┘            │
│                                              │
│ image.shape = (1, 480, 640, 3)              │
│ image.dtype = torch.uint8                    │
│                                              │
│ state.shape = (1, 9)                         │
│                                              │
│ state =                                      │
│ [ 0.00, -0.78, 0.00, ... ]                  │
│                                              │
└──────────────────────────────────────────────┘
```

This is going to be very useful later when we connect GR00T.

---



# D1 — Define the state

For this first exercise, let's keep it simple:

```python
state = robot.data.joint_pos
```

Then:

```python
print("state.shape:", state.shape)
print("state:", state)
```

You should get something conceptually like:

```text
state.shape: torch.Size([1, 9])

state:
tensor([
    [ 0.0000,
     -0.7854,
      0.0000,
     -2.3562,
      0.0000,
      1.5708,
      0.7854,
      0.0400,
      0.0400]
])
```

---



# D2 — Define the image

```python
image = camera.data.output["rgb"]
```

Then:

```python
print("image.shape:", image.shape)
print("image.dtype:", image.dtype)
```

Example:

```text
image.shape: torch.Size([1, 480, 640, 3])
image.dtype: torch.uint8
```

---



# D3 — Remove the batch dimension

For displaying one image:

```python
image_np = image[0].cpu().numpy()
```

Now:

```text
image_np.shape
```

will be:

```text
(480, 640, 3)
```

That's exactly the sort of array you're familiar with from OpenCV.

---



# D4 — Display the image

For the simplest first test, use Matplotlib.

Add:

```python
import matplotlib.pyplot as plt
```

Then:

```python
plt.imshow(image_np)
plt.axis("off")
plt.show()
```

You should see the actual camera view.

However, **don't use** `plt.show()` **every simulation timestep**.

That will stop/block the simulation.

Instead, for the first test, display only once.

For example:

```python
if step_count == 100:
    image_np = camera.data.output["rgb"][0].cpu().numpy()

    plt.imshow(image_np)
    plt.axis("off")
    plt.show()
```

---



# D5 — Better: save the image

I actually recommend this first because it's easier to debug.

```python
from PIL import Image
```

Then:

```python
image_np = camera.data.output["rgb"][0].cpu().numpy()

Image.fromarray(image_np).save("franka_camera.png")
```

Run your simulation.

Then:

```bash
ls -lh franka_camera.png
```

and open it.

On your Linux desktop:

```bash
xdg-open franka_camera.png
```

Now you have:

```text
Isaac Sim camera
       ↓
RGB tensor
       ↓
NumPy
       ↓
PNG
       ↓
your eyes
```

---



# D6 — Print actual pixel values

Because you specifically want to understand the observation rather than treat it as magic, also print:

```python
print("image.shape:", image.shape)
print("image.dtype:", image.dtype)
print("image.min:", image.min().item())
print("image.max:", image.max().item())
```

You might get:

```text
image.shape: torch.Size([1, 480, 640, 3])
image.dtype: torch.uint8
image.min: 0
image.max: 255
```

Then inspect one pixel:

```python
print(image[0, 100, 100])
```

Maybe:

```text
tensor([132, 145, 171], dtype=torch.uint8)
```

That literally means:

```text
pixel (100,100)

R = 132
G = 145
B = 171
```

---



# D7 — Your complete observation now

At the end of Checkpoint D, you should be able to say:

```text
At simulation timestep N:

camera observation:
    shape = (1, H, W, 3)
    dtype = uint8

robot observation:
    shape = (1, 9)
    dtype = float32

robot state:
    [
      joint1,
      joint2,
      joint3,
      joint4,
      joint5,
      joint6,
      joint7,
      gripper1,
      gripper2
    ]
```

So:

```text
                SIMULATOR
                    │
          ┌─────────┴──────────┐
          │                    │
          ▼                    ▼
       CAMERA                ROBOT
          │                    │
          ▼                    ▼
    RGB observation        joint state
          │                    │
          ▼                    ▼
 (1,H,W,3)              (1,9)
 uint8                   float
```

That is **exactly the conceptual foundation we need for VLA**.

---



# One important distinction before we move to GR00T

At this point our Franka observation is **not yet DROID format**.

We currently have:

```text
RGB
+
Franka joint positions
```

DROID expects:

```text
exterior_image_1_left
wrist_image_left

+

eef_9d
gripper_position
joint_position

+

language
```

with:

```text
9 + 1 + 7 = 17 state dimensions
```

and the corresponding 17-D action representation. ([GitHub](https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com))

So don't try to feed:

```python
robot.data.joint_pos
```

directly into GR00T yet.

We first need to build the **DROID observation adapter**.

---



# Where you should be after these steps

Your project can now look like:

```text
~/groot-poc/
│
├── IsaacLab/
│   ├── ...
│   └── ...
│
├── my_franka.py
└── franka_camera.png
```

And your conceptual system is:

```text
                  ISAAC LAB
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
       FRANKA                  CAMERA
          │                       │
          │                       ▼
          │                 RGB image
          │                       │
          ▼                       │
    joint positions              │
          │                       │
          └───────────┬───────────┘
                      ▼
                 OBSERVATION
                      │
                      ▼
               [next checkpoint]
                      │
                      ▼
               DROID ADAPTER
                      │
                      ▼
                 GR00T N1.7
```



## The next checkpoint I recommend

**Do not connect GR00T immediately.**

The next step should be a small but very important **Checkpoint E: make the simulated Franka observations look like the DROID observation dictionary**:

```python
{
    "video": {
        "exterior_image_1_left": ...,
        "wrist_image_left": ...,
    },

    "state": {
        "eef_9d": ...,
        "gripper_position": ...,
        "joint_position": ...,
    },

    "language": {
        "annotation": {
            "language_instruction": "..."
        }
    }
}
```

Then we'll print every key, shape, dtype and value.

After that, we can put **the real** `GR00T-N1.7-3B` **DROID policy in the loop** and inspect its **17-D action chunk before executing anything**. That will give you a clean bridge from the DROID inference you've already done to the simulated robot.

The official GR00T DROID interface is exactly the reason for doing this adapter explicitly: NVIDIA documents the two camera inputs, 17-D state, language instruction, and 17-D action structure for `OXE_DROID_RELATIVE_EEF_RELATIVE_JOINT`. ([GitHub](https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com))

---



# Wrist Cam

Yes. This is the right next step.

The key idea is **not merely to add another camera somewhere near the Franka**. We want a **wrist camera whose pose is parented to a moving Franka link**, so that when the arm/gripper moves, the camera moves with it.

That corresponds to the DROID concept of:

```text
exterior_image_1_left   ← fixed external camera
wrist_image_left        ← camera attached to robot
```

The current GR00T DROID configuration expects exactly those two video keys, plus `eef_9d`, `gripper_position`, and `joint_position`. ([GitHub](https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com))

And Isaac Lab has a native `CameraCfg` mechanism specifically for attaching a camera under a robot body/link using a relative offset. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/04_sensors/add_sensors_on_robot.html?utm_source=chatgpt.com))

So let's build this incrementally.

---



# Target setup

You already have:

```text
                 external camera
                       │
                       ▼
                  ┌────────┐
                  │        │
                  │ FRANKA │
                  │        │
                  └────────┘
```

We want:

```text
                 external camera
                       │
                       ▼
                  ┌────────┐
                  │        │
                  │ FRANKA │
                  │      ╲ │
                  │       ╲│
                  └────────╲┘
                           ▲
                       wrist camera
```

More precisely:

```text
                  Fixed camera
                      │
                      │
                      ▼
              ┌──────────────┐
              │    FRANKA    │
              │              │
              │       arm ───●─── gripper
              │                    │
              └────────────────────┘
                                   │
                              [WRIST CAM]
                                   │
                                   ▼
                              RGB image
```

Eventually:

```text
DROID-like simulation
────────────────────────────────────────

external camera ──────→ exterior_image_1_left
                              │
                              │
wrist camera ──────────→ wrist_image_left
                              │
Franka joints ─────────→ joint_position
                              │
Franka gripper ────────→ gripper_position
                              │
EEF pose ──────────────→ eef_9d
                              │
language ──────────────→ instruction
                              │
                              ▼
                       GR00T N1.7
                              │
                              ▼
                       DROID action
```

---



# Step 1 — Don't modify your working camera yet

First, make a copy of the script you already used successfully for Checkpoint C/D.

For example:

```bash
cd ~/groot-poc

cp my_franka.py my_franka_wrist_camera.py
```

If your existing script has another name, use that instead.

The important thing is:

```text
my_franka.py
    ↓
known-good
```

and:

```text
my_franka_wrist_camera.py
    ↓
experimental
```

That way you can always go back.

---



# Step 2 — Identify the Franka link we want to attach to

This is important.

A camera needs a **parent frame**.

We don't want:

```text
camera
  ↓
world
```

because that produces a fixed camera.

We want:

```text
Franka wrist link
       ↓
    camera
```

The camera will therefore inherit the motion of that link.

For the first experiment, I recommend attaching it to the **end-effector/wrist area**, rather than literally attaching it to the gripper finger.

You want something conceptually like:

```text
               forearm
                  │
                  ●
                  │
              wrist link
                  │
             ┌────┴────┐
             │  camera │
             └─────────┘
                  │
                  ▼
               gripper
```

This is more stable than putting the camera on a finger.

---



# Step 3 — Find your Franka prim structure

This is one place where I don't want you to blindly copy a prim path from an old tutorial.

Run your working Franka script.

Then, in another terminal, you can inspect the USD hierarchy from the Isaac Sim UI, or add a temporary print/debug section to your script.

You are looking for something resembling:

```text
/World/envs/env_0/Robot
```

and underneath:

```text
Robot
├── panda_link0
├── panda_link1
├── panda_link2
├── panda_link3
├── panda_link4
├── panda_link5
├── panda_link6
├── panda_link7
├── panda_hand
├── panda_leftfinger
└── panda_rightfinger
```

The exact hierarchy can differ depending on the asset/configuration.

The important part is finding the **rigid body link at the wrist/end-effector**.

Usually `panda_hand` is the useful attachment point.

---



# Step 4 — Understand what Isaac Lab's camera attachment means

Isaac Lab's current camera tutorial uses this pattern:

```python
CameraCfg(
    prim_path="{ENV_REGEX_NS}/Robot/base/front_cam",
    ...
    offset=CameraCfg.OffsetCfg(...)
)
```

The important part is:

```text
{ENV_REGEX_NS}/Robot/base/front_cam
                         │
                         └── camera is under "base"
```

The documentation explicitly describes this as creating the camera relative to the parent robot frame, with the `offset` defining the camera's translation/rotation relative to that parent. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/04_sensors/add_sensors_on_robot.html?utm_source=chatgpt.com))

Therefore we can change:

```text
Robot/base/front_cam
```

to something conceptually like:

```text
Robot/panda_hand/wrist_cam
```

Then:

```text
panda_hand
     │
     └── wrist_cam
```

So:

```text
panda_hand moves
       ↓
wrist_cam moves
       ↓
camera view changes
```

That's exactly what we want.

---



# Step 5 — Add a second camera configuration

You already have something like:

```python
camera = CameraCfg(
    ...
)
```

for your external camera.

**Do not remove it.**

Instead create a second configuration:

```python
wrist_camera = CameraCfg(
    prim_path="{ENV_REGEX_NS}/Robot/panda_hand/wrist_cam",
    update_period=0.1,
    height=480,
    width=640,
    data_types=["rgb"],
    spawn=sim_utils.PinholeCameraCfg(
        focal_length=24.0,
        focus_distance=400.0,
        horizontal_aperture=20.955,
        clipping_range=(0.1, 1.0e5),
    ),
    offset=CameraCfg.OffsetCfg(
        pos=(0.10, 0.0, 0.05),
        rot=(1.0, 0.0, 0.0, 0.0),
        convention="ros",
    ),
)
```

**Don't assume those position/rotation numbers are correct for your Panda.**

They're only a starting point.

The important structure is:

```python
prim_path="{ENV_REGEX_NS}/Robot/panda_hand/wrist_cam"
```

and:

```python
offset=CameraCfg.OffsetCfg(...)
```

Isaac Lab explicitly supports this parent-relative camera configuration. ([Isaac Sim](https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/04_sensors/add_sensors_on_robot.html?utm_source=chatgpt.com))

---



# Step 6 — Be careful about the camera coordinate convention

This is one of the places robotics becomes confusing.

Your camera has its own coordinate system.

The camera needs to point **forward from the wrist**.

You may initially get:

```text
camera → floor
```

or:

```text
camera → ceiling
```

or:

```text
camera → robot arm
```

That's normal.

We will tune:

```python
rot=(...)
```

until the camera points approximately where the DROID wrist camera should point.

Don't worry about perfect DROID matching yet.

First goal:

> **The camera physically follows the gripper and looks toward the workspace.**

---



# Step 7 — Instantiate the wrist camera

Where your current script creates the external camera:

```python
camera = Camera(camera_cfg)
```

add:

```python
wrist_camera = Camera(wrist_camera_cfg)
```

So conceptually:

```python
external_camera = Camera(external_camera_cfg)

wrist_camera = Camera(wrist_camera_cfg)
```

You now have:

```text
Camera #1
    ↓
external camera

Camera #2
    ↓
wrist camera
```

---



# Step 8 — Initialize both cameras

Where you initialize the existing camera, make sure the wrist camera is initialized too.

Depending on the structure of your current script, this may simply happen when the scene is initialized.

Then inside your simulation loop:

```python
external_camera.update(dt)
wrist_camera.update(dt)
```

You should now be updating two sensors.

---



# Step 9 — Read both RGB images

Your existing camera probably has something like:

```python
image = camera.data.output["rgb"]
```

Now add:

```python
wrist_image = wrist_camera.data.output["rgb"]
```

You should have:

```python
external_image = external_camera.data.output["rgb"]
wrist_image = wrist_camera.data.output["rgb"]
```

Then:

```python
print("external:", external_image.shape)
print("wrist:", wrist_image.shape)
```

Expected conceptually:

```text
external: torch.Size([1, 480, 640, 3])
wrist:    torch.Size([1, 480, 640, 3])
```

The exact resolution is whatever you configured.

---



# Step 10 — Save the wrist image

Do this before trying to display it continuously.

```python
wrist_image_np = wrist_image[0].cpu().numpy()

Image.fromarray(wrist_image_np).save(
    "wrist_camera.png"
)
```

Run:

```bash
./isaaclab.sh -p my_franka_wrist_camera.py
```

After the simulation reaches your chosen timestep:

```bash
xdg-open wrist_camera.png
```

You should see what the wrist-mounted camera sees.

---



# Step 11 — Now prove that the camera actually follows the arm

This is the **critical test**.

Don't just look at the image.

Move the Franka.

For example:

```text
initial:

          camera
             ↓
             ● gripper
            /
           /
          /
         /
        base
```

Then move the arm:

```text
             camera
                ↓
                ● gripper
                 \
                  \
                   \
                    ●
                   /
                  /
                base
```

The camera itself should have moved with the wrist.

---



# Step 12 — Make the test visually obvious

Use a large arm movement.

For example:

```text
POSITION A

             ●
            /
           /
          /
         /
        ●
```

Then:

```text
POSITION B

        ●
         \
          \
           \
            ●
```

The wrist camera's view should change dramatically.

If the camera view doesn't change, the camera is probably still parented to the world rather than the robot link.

---



# Step 13 — Verify the camera's USD hierarchy

In Isaac Sim's Stage panel, you ideally want something like:

```text
World
└── envs
    └── env_0
        └── Robot
            ├── panda_link0
            ├── panda_link1
            ├── ...
            ├── panda_hand
            │   └── wrist_cam
            ├── panda_leftfinger
            └── panda_rightfinger
```

This is what you want.

Not:

```text
World
├── external_camera
├── wrist_camera
└── Robot
```

The latter means your "wrist camera" is actually another world-fixed camera.

---



# Step 14 — Get the camera looking in the correct direction

Now we tune:

```python
offset=CameraCfg.OffsetCfg(
    pos=(...),
    rot=(...),
    convention="ros",
)
```

There are two things to tune:

### Position

```text
pos=(x, y, z)
```

moves the camera relative to the wrist.

For example:

```text
             camera
               ●
              /
             /
       wrist●
```



### Rotation

```text
rot=(...)
```

changes where the camera looks.

You want approximately:

```text
                  camera
                    ●
                   /
                  /
                 /
                ▼
             workspace
```

rather than:

```text
                  camera
                    ●
                    │
                    ▼
                   floor
```

---



# Step 15 — Make the wrist camera resemble DROID

The important thing is not initially to reproduce the physical DROID camera model perfectly.

What we want is the **same observation concept**:

```text
DROID:

external camera
      +
wrist camera
      +
robot state
      +
language
```

The current GR00T DROID modality configuration expects:

```text
video:
    exterior_image_1_left
    wrist_image_left

state:
    eef_9d
    gripper_position
    joint_position

language:
    annotation.language.language_instruction
```

and the DROID action is 40 steps of:

```text
eef_9d
gripper_position
joint_position
```

with the corresponding relative/absolute representations. ([GitHub](https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com))

So your simulation should eventually produce:

```python
observation = {
    "video": {
        "exterior_image_1_left": external_image,
        "wrist_image_left": wrist_image,
    },

    "state": {
        "eef_9d": ...,
        "gripper_position": ...,
        "joint_position": ...,
    },

    "language": {
        "annotation": {
            "language_instruction": "pick up the cube"
        }
    },
}
```

**But don't build this dictionary yet.**

First make sure the two cameras work independently.

---



# Step 16 — Match DROID's image size later

For your first camera test:

```text
640 × 480
```

is perfectly fine.

Once everything works, we'll resize to the actual GR00T/DROID inference format.

A current DROID deployment reference uses:

```text
HWC
uint8
180 × 320
```

for the camera images. ([GitHub](https://github.com/NVlabs/RoboLab/blob/main/policies/gr00t/README.md?utm_source=chatgpt.com))

So eventually:

```text
Isaac camera
    ↓
640 × 480 × 3
    ↓
resize
    ↓
180 × 320 × 3
    ↓
uint8
    ↓
GR00T
```

Don't resize yet.

It makes debugging harder.

---



# Step 17 — Your first two-camera observation test

Once the wrist camera is working, add this:

```python
external_image = external_camera.data.output["rgb"]
wrist_image = wrist_camera.data.output["rgb"]

print()
print("========== OBSERVATION ==========")

print("external_image")
print("  shape :", external_image.shape)
print("  dtype :", external_image.dtype)

print("wrist_image")
print("  shape :", wrist_image.shape)
print("  dtype :", wrist_image.dtype)

print("=================================")
```

You should see something like:

```text
========== OBSERVATION ==========

external_image
  shape : torch.Size([1, 480, 640, 3])
  dtype : torch.uint8

wrist_image
  shape : torch.Size([1, 480, 640, 3])
  dtype : torch.uint8

=================================
```

---



# Step 18 — Display BOTH images side by side

This is much more useful than looking at them separately.

Use:

```python
import matplotlib.pyplot as plt
```

Then:

```python
external_np = external_image[0].cpu().numpy()
wrist_np = wrist_image[0].cpu().numpy()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].imshow(external_np)
axes[0].set_title("External Camera")
axes[0].axis("off")

axes[1].imshow(wrist_np)
axes[1].set_title("Wrist Camera")
axes[1].axis("off")

plt.tight_layout()
plt.show()
```

You should get:

```text
┌─────────────────────────┬─────────────────────────┐
│     EXTERNAL CAMERA     │      WRIST CAMERA       │
│                         │                         │
│                         │       gripper           │
│       whole arm        │          ↓              │
│          ↓              │       workspace         │
│       FRANKA            │                         │
│                         │                         │
└─────────────────────────┴─────────────────────────┘
```

This is the first really meaningful visual checkpoint.

---



# Step 19 — Move the arm while watching the wrist image

Now modify your robot movement so the Franka moves through several positions.

For example:

```text
pose 1
  ↓
pose 2
  ↓
pose 3
  ↓
pose 4
```

At every pose:

```text
external camera
    ↓
view changes somewhat

wrist camera
    ↓
view changes significantly
```

The wrist camera should behave as though you physically bolted a camera onto the robot's wrist.

That's the behavior we want.

---



# Step 20 — Don't attach the camera to the gripper finger

This is worth emphasizing.

Don't do:

```text
panda_leftfinger
      ↓
camera
```

for this experiment.

Use:

```text
panda_hand
      ↓
wrist_cam
```

or another stable wrist/end-effector link.

The DROID wrist camera is conceptually a camera mounted around the wrist/gripper area, not something that needs to move with an individual finger.

---



# Step 21 — Your simulation now looks like this

Once this works:

```text
                         Isaac Lab
                            │
             ┌──────────────┴──────────────┐
             │                             │
             ▼                             ▼
          Franka                      external camera
             │                             │
             │                             ▼
             │                    exterior_image_1_left
             │
             ├── panda_hand
             │       │
             │       └── wrist_cam
             │               │
             │               ▼
             │        wrist_image_left
             │
             ├── 7 arm joints
             │
             └── gripper
```

That's already **very close conceptually to the visual portion of DROID**.

---



# Step 22 — One important difference: real DROID vs our simulation

Don't expect the two images to look identical to NVIDIA's real DROID videos.

The real DROID setup has its own:

- camera intrinsics
- camera placement
- resolution
- robot geometry
- lighting
- workspace
- camera distortion
- coordinate conventions

We're currently trying to reproduce the **interface**, not perfectly reproduce the physical dataset.

That distinction matters.

---



# Step 23 — Why this is enough for GR00T

The current base GR00T N1.7 checkpoint has the DROID pretrain embodiment baked in:

```text
OXE_DROID_RELATIVE_EEF_RELATIVE_JOINT
```

so it can perform DROID inference without additional training. NVIDIA also provides the fine-tuned:

```text
nvidia/GR00T-N1.7-DROID
```

checkpoint. ([GitHub](https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com))

So your eventual pipeline can be:

```text
                 SIMULATION
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
 external        wrist          Franka
 camera          camera          state
       │             │             │
       ▼             ▼             ▼
 exterior_1      wrist        eef/joints/
                                  gripper
       │             │             │
       └─────────────┼─────────────┘
                     │
                 language
                     │
                     ▼
             ┌───────────────┐
             │  GR00T N1.7   │
             │    DROID      │
             └───────┬───────┘
                     │
                     ▼
               17-D actions
                     │
                     ▼
              Isaac Lab robot
                     │
                     ▼
               new observation
                     │
                     └───────────────→ GR00T
```

---



# The next checkpoint I recommend

Once you have the wrist camera working, **don't immediately run GR00T**.

Do one more very controlled checkpoint:

### Checkpoint E — DROID observation adapter

We take what you now have:

```text
external RGB
wrist RGB
Franka joints
Franka gripper
Franka end-effector pose
```

and explicitly construct:

```python
{
    "video": {
        "exterior_image_1_left": ...,
        "wrist_image_left": ...,
    },
    "state": {
        "eef_9d": ...,
        "gripper_position": ...,
        "joint_position": ...,
    },
    "language": {
        "annotation": {
            "language_instruction": "..."
        }
    }
}
```

Then print:

```text
video
 ├── exterior_image_1_left
 │     shape = ?
 │     dtype = ?
 │
 └── wrist_image_left
       shape = ?
       dtype = ?

state
 ├── eef_9d
 │     shape = (9,)
 │     values = [...]
 │
 ├── gripper_position
 │     shape = (1,)
 │     value = [...]
 │
 └── joint_position
       shape = (7,)
       values = [...]

language
 └── "pick up the cube"
```

**That is the point where your Isaac Lab simulation and the actual DROID GR00T interface meet.**

Then the following checkpoint can be:

```text
Checkpoint F

DROID observation
       ↓
GR00T N1.7
       ↓
predicted 40-step action chunk
       ↓
PRINT ONLY
       ↓
inspect the 17-D actions
```

Only after that would I let the GR00T actions actually control the simulated Franka. That separation will make debugging dramatically easier. ([GitHub](https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com))