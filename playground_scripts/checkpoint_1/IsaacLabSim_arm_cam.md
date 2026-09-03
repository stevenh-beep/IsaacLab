Yes. Since you already completed **Checkpoint A** and the Cartpole version of B, I would now move to a **real robotic arm + gripper**, and then add a camera and inspect exactly what Isaac Lab produces.

One important correction to the earlier roadmap: **for these checkpoints, I would use Franka Panda first, not try to force the DROID embodiment onto an Isaac Lab robot yet.** Franka is already a built-in Isaac Lab manipulation asset, has 7 arm joints + gripper, and Isaac Lab has official examples for both joint-level control and task-space control. ([Isaac Sim][1])

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

Isaac Lab includes Franka as one of its built-in fixed-arm robots. ([Isaac Sim][1])

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

and uses a Franka configuration called `FRANKA_PANDA_HIGH_PD_CFG`. ([Isaac Sim][2])

---

# B2 — Run the Franka differential-IK example

Try:

```bash
./isaaclab.sh -p scripts/tutorials/05_controllers/run_diff_ik.py
```

If your checkout contains that tutorial at that path, this should open Isaac Sim with the Franka arm.

The current official tutorial creates a Franka robot and a differential inverse-kinematics controller. ([Isaac Sim][2])

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

The official Isaac Lab example uses `DifferentialIKController` for exactly this purpose. ([Isaac Sim][2])

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

Isaac Lab's articulation tutorial specifically demonstrates reading joint state and applying commands to articulated robots. ([Isaac Sim][3])

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

for the Panda. ([Isaac Sim][2])

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
~/groot-poc/my_franka.py
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

Isaac Lab's camera system is a renderer-backed sensor. The camera can output RGB, depth, normals and other data. ([Isaac Sim][4])

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

The current Isaac Lab documentation includes a `run_usd_camera.py` tutorial specifically for using a camera sensor. ([Isaac Sim][5])

---

# C2 — Run the official camera example first

Try:

```bash
./isaaclab.sh -p \
scripts/tutorials/04_sensors/run_usd_camera.py \
--enable_cameras
```

The current official example documents this exact GUI invocation. ([Isaac Sim][5])

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

The current Isaac Lab camera documentation explicitly specifies this `(num_cameras, height, width, 3)` RGB format and `torch.uint8` type. ([Isaac Sim][4])

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

The exact spawn configuration should follow the camera example in your installed Isaac Lab version; the current API supports RGB through `data_types=["rgb"]`. ([Isaac Sim][4])

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

as its two visual inputs. ([GitHub][6])

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

The current Isaac Lab API documents exactly this pattern for camera output. ([Isaac Sim][4])

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

However, **don't use `plt.show()` every simulation timestep**.

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

and the corresponding 17-D action representation. ([GitHub][6])

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

After that, we can put **the real `GR00T-N1.7-3B` DROID policy in the loop** and inspect its **17-D action chunk before executing anything**. That will give you a clean bridge from the DROID inference you've already done to the simulated robot.

The official GR00T DROID interface is exactly the reason for doing this adapter explicitly: NVIDIA documents the two camera inputs, 17-D state, language instruction, and 17-D action structure for `OXE_DROID_RELATIVE_EEF_RELATIVE_JOINT`. ([GitHub][6])

[1]: https://isaac-sim.github.io/IsaacLab/?utm_source=chatgpt.com "Welcome to Isaac Lab! — Isaac Lab Documentation"
[2]: https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/05_controllers/run_diff_ik.html?utm_source=chatgpt.com "Using a task-space controller — Isaac Lab Documentation"
[3]: https://isaac-sim.github.io/IsaacLab/develop/source/tutorials/01_assets/run_articulation.html?utm_source=chatgpt.com "Interacting with an articulation — Isaac Lab Documentation"
[4]: https://isaac-sim.github.io/IsaacLab/develop/source/overview/core-concepts/sensors/camera.html?utm_source=chatgpt.com "Camera — Isaac Lab Documentation"
[5]: https://isaac-sim.github.io/IsaacLab/main/source/how-to/save_camera_output.html?utm_source=chatgpt.com "Saving rendered images and 3D re-projection — Isaac Lab Documentation"
[6]: https://github.com/NVIDIA/Isaac-GR00T/blob/main/examples/DROID/README.md?utm_source=chatgpt.com "Isaac-GR00T/examples/DROID/README.md at main · NVIDIA/Isaac-GR00T · GitHub"

