# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""
This script demonstrates how to use the differential inverse kinematics controller with the simulator.

The differential IK controller can be configured in different modes. It uses the Jacobians computed by
PhysX. This helps perform parallelized computation of the inverse kinematics.

.. code-block:: bash

    # Usage
    ./isaaclab.sh -p scripts/tutorials/05_controllers/run_diff_ik.py --viz kit

    # Usage w/ single cam
    ./isaaclab.sh -p playground_scripts/checkpoint_1/run_diff_ik_my_franka_dual_cam.py --robot franka_panda --num_envs 2 --enable_cameras --save --viz kit
"""

"""Launch Isaac Sim Simulator first."""

import argparse

from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="Tutorial on using the differential IK controller.")
parser.add_argument("--robot", type=str, default="franka_panda", help="Name of the robot.")
parser.add_argument("--num_envs", type=int, default=128, help="Number of environments to spawn.")

parser.add_argument(
    "--save",
    action="store_true",
    default=False,
    help="Save RGB (and other) images from the added camera.",
)

parser.add_argument(
    "--save_interval",
    type=int,
    default=10,
    help="Save a fixed+wrist image pair every N simulation steps (only when --save is set).",
)

# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
# parse the arguments
args_cli = parser.parse_args()

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import AssetBaseCfg
from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.managers import SceneEntityCfg
from isaaclab.markers import VisualizationMarkers
from isaaclab.markers.config import FRAME_MARKER_CFG
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR
from isaaclab.utils.configclass import configclass
from isaaclab.utils.math import subtract_frame_transforms
from isaaclab.assets import RigidObjectCfg

##
# Pre-defined configs
##
from isaaclab_assets import FRANKA_PANDA_HIGH_PD_CFG, UR10_CFG  # isort:skip

import os
import omni.replicator.core as rep

from isaaclab.sensors import Camera, CameraCfg
from isaaclab.utils import convert_dict_to_backend
# (optional, only if you want the same colourised segmentation options as the reference)
from isaaclab_physx.renderers import IsaacRtxRendererCfg

import matplotlib.pyplot as plt
from PIL import Image
import numpy as np


@configclass
class TableTopSceneCfg(InteractiveSceneCfg):
    """Configuration for a cart-pole scene."""

    # ground plane
    ground = AssetBaseCfg(
        prim_path="/World/defaultGroundPlane",
        spawn=sim_utils.GroundPlaneCfg(),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, -1.05)),
    )

    # lights
    dome_light = AssetBaseCfg(
        prim_path="/World/Light", spawn=sim_utils.DomeLightCfg(intensity=3000.0, color=(0.75, 0.75, 0.75))
    )

    # mount
    table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=sim_utils.UsdFileCfg(
            usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Mounts/Stand/stand_instanceable.usd", scale=(2.0, 2.0, 2.0)
        ),
    )

    # articulation
    if args_cli.robot == "franka_panda":
        robot = FRANKA_PANDA_HIGH_PD_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
    elif args_cli.robot == "ur10":
        robot = UR10_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
    else:
        raise ValueError(f"Robot {args_cli.robot} is not supported. Valid: franka_panda, ur10")

    # Fixed external camera that looks at the table / Franka workspace
    fixed_camera = CameraCfg(
        prim_path="{ENV_REGEX_NS}/FixedCamera",          # one camera per env
        update_period=0.0,                                # update every physics step
        height=480,
        width=640,
        debug_vis=True,
        data_types=["rgb"],                               # start minimal; add "distance_to_image_plane" etc. later if needed
        # Optional – match the reference script’s colourisation behaviour
        # renderer_cfg=IsaacRtxRendererCfg(
        #     colorize_semantic_segmentation=True,
        #     colorize_instance_id_segmentation=True,
        #     colorize_instance_segmentation=True,
        # ),
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=24.0,
            focus_distance=400.0,
            horizontal_aperture=20.955,
            clipping_range=(0.1, 1.0e5),
        ),
        # Pose relative to each environment origin – looks down at the table from a good viewing angle
        offset=CameraCfg.OffsetCfg(
            pos=(0.0, 0.0, 0.0),                          # eye position
            rot=(1.0, 0.0, 0.0, 0.0),       # ROS convention quaternion looking toward origin
            convention="ros",
        ),
    )

    # Wrist / in-hand camera (standard Isaac Lab Franka pattern)
    wrist_camera = CameraCfg(
        prim_path="{ENV_REGEX_NS}/Robot/panda_hand/wrist_cam",
        update_period=0.0,                                # every physics step (matches fixed)
        height=480,
        width=640,
        debug_vis=True,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=24.0,
            focus_distance=400.0,
            horizontal_aperture=20.955,
            clipping_range=(0.1, 1.0e5),
        ),
        # Small offset in front of the hand, looking outward (ROS convention)
        # This is the canonical offset used in Isaac Lab stack / visuomotor examples.
        offset=CameraCfg.OffsetCfg(
            pos=(0.0, 0.12, 0.1),       
            rot=(1.0, 0.0, 0.0, 0.0),       
            convention="ros",
        ),
    )

    tall_marker = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Marker",
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.55, 0.0, 0.30),          # slightly in front of the default workspace, on the table
            rot=(0.0, 0.0, 0.0, 0.0),
        ),
        spawn=sim_utils.CuboidCfg(
            size=(0.08, 0.08, 0.60),         # tall thin pillar (0.6 m high)
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                max_depenetration_velocity=5.0,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(1.0, 0.2, 0.0),   # bright orange – very visible
                metallic=0.1,
            ),
        ),
    )


def run_simulator(sim: sim_utils.SimulationContext, scene: InteractiveScene):
    """Runs the simulation loop."""
    # Extract scene entities
    # note: we only do this here for readability.
    robot = scene["robot"]
    fixed_camera: Camera = scene["fixed_camera"]
    wrist_camera: Camera  = scene["wrist_camera"]

    # # Optional writer (only if --save)
    # if args_cli.save:
    #     output_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "output", "franka_camera")
    #     os.makedirs(output_dir, exist_ok=True)
    #     rep_writer = rep.BasicWriter(
    #         output_dir=output_dir,
    #         frame_padding=0,
    #         # pass the colourise flags if you enabled them in CameraCfg
    #         # colorize_instance_id_segmentation=...,
    #         # colorize_instance_segmentation=...,
    #         # colorize_semantic_segmentation=...,
    #     )

    if args_cli.save:
        base_output_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "output",
            "franka_dual_cam",
        )
        fixed_dir = os.path.join(base_output_dir, "fixed")
        wrist_dir = os.path.join(base_output_dir, "wrist")
        os.makedirs(fixed_dir, exist_ok=True)
        os.makedirs(wrist_dir, exist_ok=True)

        combined_dir = os.path.join(base_output_dir, "combined")
        os.makedirs(combined_dir, exist_ok=True)

        print(f"[INFO] Saving image pairs every {args_cli.save_interval} steps to:\n"
            f"       {fixed_dir}\n"
            f"       {wrist_dir}"
            f"       {combined_dir}")

    # Create controller
    diff_ik_cfg = DifferentialIKControllerCfg(command_type="pose", use_relative_mode=False, ik_method="dls")
    diff_ik_controller = DifferentialIKController(diff_ik_cfg, num_envs=scene.num_envs, device=sim.device)

    # Markers
    frame_marker_cfg = FRAME_MARKER_CFG.copy()
    frame_marker_cfg.markers["frame"].scale = (0.02, 0.02, 0.02)
    ee_marker = VisualizationMarkers(frame_marker_cfg.replace(prim_path="/Visuals/ee_current"))
    goal_marker = VisualizationMarkers(frame_marker_cfg.replace(prim_path="/Visuals/ee_goal"))

    cam_marker_cfg = FRAME_MARKER_CFG.copy()
    cam_marker_cfg.markers["frame"].scale = (0.06, 0.06, 0.06)  # nice visible size
    wrist_cam_marker = VisualizationMarkers(
        cam_marker_cfg.replace(prim_path="/Visuals/wrist_cam_frame")
    )

    # Define goals for the arm (x,y,z,qx,qy,qz,qw)
    ee_goals = [
        [0.5, 0.5, 0.7, 0, 0.707, 0, 0.707],
        # [0.5, -0.4, 0.6, 0.707, 0, 0, 0.707],
        # [0.5, 0, 0.5, 1.0, 0.0, 0.0, 0.0],
    ]
    ee_goals = torch.tensor(ee_goals, device=sim.device)
    # Track the given command
    current_goal_idx = 0
    # Create buffers to store actions
    ik_commands = torch.zeros(scene.num_envs, diff_ik_controller.action_dim, device=robot.device)
    ik_commands[:] = ee_goals[current_goal_idx]

    # gripper control
    gripper_open = 0.08
    gripper_close = 0.0002
    position_threshold = 0.02

    # 2 is because - 
    # joint names: ['panda_joint1', 'panda_joint2', 'panda_joint3', 'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7', 'panda_finger_joint1', 'panda_finger_joint2']
    # 'panda_finger_joint1', 'panda_finger_joint2' there are 2 joints
    gripper_commands = torch.zeros(scene.num_envs, 2, device=robot.device)
    gripper_commands[:] = gripper_close

    # Specify robot-specific parameters
    if args_cli.robot == "franka_panda":
        robot_entity_cfg = SceneEntityCfg("robot", joint_names=["panda_joint.*"], body_names=["panda_hand"])
        gripper_entity_cfg = SceneEntityCfg("robot", joint_names = ['panda_finger_joint.*'])
    elif args_cli.robot == "ur10":
        robot_entity_cfg = SceneEntityCfg("robot", joint_names=[".*"], body_names=["ee_link"])
        gripper_entity_cfg = None
    else:
        raise ValueError(f"Robot {args_cli.robot} is not supported. Valid: franka_panda, ur10")
    # Resolving the scene entities
    robot_entity_cfg.resolve(scene)
    if gripper_entity_cfg is not None:
        gripper_entity_cfg.resolve(scene)
    # Obtain the frame index of the end-effector
    # For a fixed base robot, the frame index is one less than the body index. This is because
    # the root body is not included in the returned Jacobians.
    if robot.is_fixed_base:
        ee_jacobi_idx = robot_entity_cfg.body_ids[0] - 1
    else:
        ee_jacobi_idx = robot_entity_cfg.body_ids[0]

    print("[INFO]: joint names:", robot.joint_names)
    print("[INFO]: joint positions:", robot.data.joint_pos.torch)
    print("[INFO]: joint velocities:", robot.data.joint_vel.torch)
    
    # Define simulation stepping
    sim_dt = sim.get_physics_dt()
    count = 0
    # Simulation loop
    while simulation_app.is_running():
        # reset
        if count % 150 == 0:
            # reset time
            count = 0
            # reset joint state
            joint_pos = robot.data.default_joint_pos.torch.clone()
            joint_vel = robot.data.default_joint_vel.torch.clone()
            robot.write_joint_position_to_sim_index(position=joint_pos)
            robot.write_joint_velocity_to_sim_index(velocity=joint_vel)
            robot.reset()
            # reset actions
            ik_commands[:] = ee_goals[current_goal_idx]
            joint_pos_des = joint_pos[:, robot_entity_cfg.joint_ids].clone()
            # reset controller
            diff_ik_controller.reset()
            diff_ik_controller.set_command(ik_commands)
            

            # resetting the gripper
            if gripper_entity_cfg is not None:
                gripper_commands[:] = gripper_close

            # change goal
            current_goal_idx = (current_goal_idx + 1) % len(ee_goals)
        else:
            # obtain quantities from simulation. The Jacobian DoF axis prepends
            # ``num_base_dofs`` floating-base columns (0 for fixed-base, 6 for
            # floating-base); shift the actuated-joint ids accordingly.
            jacobi_joint_ids = [j + robot.num_base_dofs for j in robot_entity_cfg.joint_ids]
            jacobian = robot.data.body_link_jacobian_w.torch[:, ee_jacobi_idx, :, jacobi_joint_ids]
            ee_pose_w = robot.data.body_pose_w.torch[:, robot_entity_cfg.body_ids[0]]
            root_pose_w = robot.data.root_pose_w.torch
            joint_pos = robot.data.joint_pos.torch[:, robot_entity_cfg.joint_ids]
            # compute frame in root frame
            ee_pos_b, ee_quat_b = subtract_frame_transforms(
                root_pose_w[:, 0:3], root_pose_w[:, 3:7], ee_pose_w[:, 0:3], ee_pose_w[:, 3:7]
            )
            # compute the joint commands
            joint_pos_des = diff_ik_controller.compute(ee_pos_b, ee_quat_b, jacobian, joint_pos)

            # setting gripper – only act after the arm has reached the goal
            if gripper_entity_cfg is not None:
                # current hand position in world frame
                current_pos = ee_pose_w[:, 0:3]
                # goal position in world frame
                goal_pos = ik_commands[:, 0:3] + scene.env_origins

                # distance between hand and goal
                pos_error = torch.norm(current_pos - goal_pos, dim=1)

                # only change gripper when close enough
                arrived = pos_error < position_threshold

                # decide open or close based on goal index (plain Python if is fine here)
                if current_goal_idx % 2 == 0:
                    desired_value = gripper_open
                else:
                    desired_value = gripper_close

                # apply the decision only to robots that have arrived
                gripper_commands[arrived] = desired_value

        # apply actions
        robot.set_joint_position_target_index(target=joint_pos_des, joint_ids=robot_entity_cfg.joint_ids)

        if gripper_entity_cfg is not None:
            robot.set_joint_position_target_index(
               target= gripper_commands,
               joint_ids = gripper_entity_cfg.joint_ids
            )
        scene.write_data_to_sim()
        # perform step
        sim.step()
        # update sim-time
        count += 1
        # update buffers
        scene.update(sim_dt)

        # Update camera data (the scene already calls sensor updates, but explicit is fine)
        fixed_camera.update(dt=sim_dt)
        wrist_camera.update(dt=sim_dt)

        # Optional: print shapes once in a while for sanity
        if count % 100 == 0:
            print(f"[Cameras] Fixed RGB: {fixed_camera.data.output['rgb'].shape} | "
          f"Wrist RGB: {wrist_camera.data.output['rgb'].shape}")

            # image_np = camera.data.output["rgb"][0].cpu().numpy()

            # plt.imshow(image_np)
            # plt.axis("off")
            # plt.show()

            # Image.fromarray(image_np).save("franka_camera.png")

        # Save (only env 0 to keep disk usage reasonable; change the slice if you want all envs)
        if args_cli.save and (count % args_cli.save_interval == 0):
            cam_id = 1
            # Fixed camera
            fixed_rgb = fixed_camera.data.output["rgb"][cam_id].cpu().numpy()   # (H, W, 3) or (H, W, 4)
            if fixed_rgb.shape[-1] == 4:                                   # drop alpha if present
                fixed_rgb = fixed_rgb[..., :3]
            Image.fromarray(fixed_rgb.astype(np.uint8)).save(
                os.path.join(fixed_dir, f"frame_{count:06d}.png")
            )

            # Wrist camera
            wrist_rgb = wrist_camera.data.output["rgb"][cam_id].cpu().numpy()
            if wrist_rgb.shape[-1] == 4:
                wrist_rgb = wrist_rgb[..., :3]
            Image.fromarray(wrist_rgb.astype(np.uint8)).save(
                os.path.join(wrist_dir, f"frame_{count:06d}.png")
            )

            # --- Combined side-by-side (fixed | wrist) ---
            # Ensure same height (they already are, but this is safe)
            h = min(fixed_rgb.shape[0], wrist_rgb.shape[0])
            fixed_rgb = fixed_rgb[:h]
            wrist_rgb = wrist_rgb[:h]
            combined = np.concatenate([fixed_rgb, wrist_rgb], axis=1)   # horizontal concat
            Image.fromarray(combined).save(
                os.path.join(combined_dir, f"frame_{count:06d}.png")
            )

        # obtain quantities from simulation
        ee_pose_w = robot.data.body_state_w.torch[:, robot_entity_cfg.body_ids[0], 0:7]
        # update marker positions
        ee_marker.visualize(ee_pose_w[:, 0:3], ee_pose_w[:, 3:7])
        goal_marker.visualize(ik_commands[:, 0:3] + scene.env_origins, ik_commands[:, 3:7])
        # Visualize the wrist camera pose (env 0)
        wrist_cam_marker.visualize(
            wrist_camera.data.pos_w[0:1],
            wrist_camera.data.quat_w_world[0:1]   # or quat_w_ros depending on your Isaac Lab version
        )


def main():
    """Main function."""
    # Load kit helper
    sim_cfg = sim_utils.SimulationCfg(dt=0.01, device=args_cli.device)
    sim = sim_utils.SimulationContext(sim_cfg)
    # Set main camera
    sim.set_camera_view([2.5, 2.5, 2.5], [0.0, 0.0, 0.0])
    # Design scene
    scene_cfg = TableTopSceneCfg(num_envs=args_cli.num_envs, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)
    # Play the simulator
    sim.reset()

    fixed_camera: Camera = scene["fixed_camera"]

    # Define the desired view (same style as the reference script)
    # These are offsets relative to each environment origin.
    eye_offset   = torch.tensor([0.6, 3.5, 0.9], device=sim.device)   # slightly in front, on the right, elevated
    target_offset = torch.tensor([0.4,  0.0, 0.45], device=sim.device)  # look at the middle of the workspace

    # Expand to all environments
    eyes    = scene.env_origins + eye_offset
    targets = scene.env_origins + target_offset

    # Apply the view (this computes the correct orientation for you)
    fixed_camera.set_world_poses_from_view(eyes, targets)

    # Now we are ready!
    print("[INFO]: Setup complete...")
    # Run the simulator
    run_simulator(sim, scene)


if __name__ == "__main__":
    # run the main function
    main()
    # close sim app
    simulation_app.close()
