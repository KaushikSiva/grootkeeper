from __future__ import annotations

import json
import os
from pathlib import Path


DEFAULT_G1_PRIM_PATH = "/World/G1"
G1_ASSET_ENV_VARS = ("G1_USD_PATH", "UNITREE_G1_USD_PATH", "GROOTKEEPER_G1_USD")
DEMO_STAGE_PATH = "trashbot_scene.usda"


def _publish_scene_state_if_ros2_available(scene_objects: list[dict[str, object]]) -> None:
    try:
        import rclpy
        from rclpy.node import Node
        from std_msgs.msg import String
    except Exception:
        print("ROS 2 Python libraries not available in this Isaac session. Skipping scene_state publish.")
        return

    class ScenePublisher(Node):
        def __init__(self) -> None:
            super().__init__("trashbot_scene_publisher")
            self.publisher = self.create_publisher(String, "/trashbot/scene_state", 10)

    rclpy.init(args=None)
    node = ScenePublisher()
    try:
        message = String()
        message.data = json.dumps(
            {
                "source": "isaac_sim_scene_script",
                "objects": scene_objects,
            }
        )
        node.publisher.publish(message)
        rclpy.spin_once(node, timeout_sec=0.2)
        print("Published /trashbot/scene_state from Isaac scene skeleton.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


def _resolve_g1_usd_path() -> str | None:
    for env_name in G1_ASSET_ENV_VARS:
        candidate = os.getenv(env_name, "").strip()
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _spawn_g1_reference(stage, g1_prim_path: str, g1_usd_path: str) -> bool:
    try:
        from pxr import UsdGeom
    except Exception:
        return False

    g1_xform = UsdGeom.Xform.Define(stage, g1_prim_path)
    g1_xform.GetPrim().GetReferences().AddReference(g1_usd_path)
    return True


def _spawn_g1_placeholder(stage, g1_prim_path: str) -> None:
    from pxr import Gf, UsdGeom

    g1_xform = UsdGeom.Xform.Define(stage, g1_prim_path)
    translate = g1_xform.AddTranslateOp()
    translate.Set(Gf.Vec3d(0.0, 0.0, 0.0))


def _set_xform(prim, translate=None, scale=None) -> None:
    from pxr import Gf, UsdGeom

    xformable = UsdGeom.Xformable(prim)
    translate_op = None
    scale_op = None
    for op in xformable.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate and translate_op is None:
            translate_op = op
        if op.GetOpType() == UsdGeom.XformOp.TypeScale and scale_op is None:
            scale_op = op
    if translate is not None:
        if translate_op is None:
            translate_op = xformable.AddTranslateOp()
        translate_op.Set(Gf.Vec3d(*translate))
    if scale is not None:
        if scale_op is None:
            scale_op = xformable.AddScaleOp()
        scale_op.Set(Gf.Vec3f(*scale))


def _set_display_color(geom, color: tuple[float, float, float]) -> None:
    from pxr import Gf

    geom.CreateDisplayColorAttr([Gf.Vec3f(*color)])


def _ensure_cube(stage, prim_path: str, translate, scale, color) -> None:
    from pxr import UsdGeom

    cube = UsdGeom.Cube.Define(stage, prim_path)
    cube.CreateSizeAttr(1.0)
    _set_xform(cube.GetPrim(), translate=translate, scale=scale)
    _set_display_color(cube, color)


def _ensure_cylinder(stage, prim_path: str, translate, radius, height, color, axis="Z") -> None:
    from pxr import UsdGeom

    cylinder = UsdGeom.Cylinder.Define(stage, prim_path)
    cylinder.CreateRadiusAttr(radius)
    cylinder.CreateHeightAttr(height)
    cylinder.CreateAxisAttr(axis)
    _set_xform(cylinder.GetPrim(), translate=translate)
    _set_display_color(cylinder, color)


def _ensure_sphere(stage, prim_path: str, translate, radius, color) -> None:
    from pxr import UsdGeom

    sphere = UsdGeom.Sphere.Define(stage, prim_path)
    sphere.CreateRadiusAttr(radius)
    _set_xform(sphere.GetPrim(), translate=translate)
    _set_display_color(sphere, color)


def _ensure_demo_environment(stage) -> None:
    _ensure_cube(
        stage,
        "/World/floor",
        translate=(0.7, 0.0, -0.03),
        scale=(2.5, 2.5, 0.03),
        color=(0.22, 0.24, 0.28),
    )
    _ensure_cube(
        stage,
        "/World/work_table",
        translate=(0.72, 0.0, 0.34),
        scale=(0.75, 1.05, 0.04),
        color=(0.42, 0.45, 0.49),
    )
    for idx, x in enumerate((0.14, 1.3)):
        for idy, y in enumerate((-0.46, 0.46)):
            _ensure_cube(
                stage,
                f"/World/work_table_leg_{idx}_{idy}",
                translate=(x, y, 0.16),
                scale=(0.04, 0.04, 0.32),
                color=(0.28, 0.3, 0.34),
            )


def _ensure_demo_lighting(stage) -> None:
    from pxr import Gf, UsdLux, UsdGeom

    dome = UsdLux.DomeLight.Define(stage, "/World/DemoDomeLight")
    dome.CreateIntensityAttr(950.0)
    dome.CreateColorAttr(Gf.Vec3f(0.92, 0.94, 1.0))

    distant = UsdLux.DistantLight.Define(stage, "/World/DemoKeyLight")
    distant.CreateIntensityAttr(750.0)
    distant.CreateAngleAttr(1.0)
    distant.CreateColorAttr(Gf.Vec3f(1.0, 0.96, 0.9))
    _set_xform(distant.GetPrim(), translate=(0.0, 0.0, 2.0))

    camera = UsdGeom.Camera.Define(stage, "/World/TrashbotCamera")
    _set_xform(camera.GetPrim(), translate=(1.75, -1.45, 1.45))


def main() -> None:
    try:
        import omni.usd
        from pxr import Gf, UsdGeom
    except Exception as exc:
        raise RuntimeError(
            "Run this inside Isaac Sim Script Editor or with the Isaac Sim Python runtime."
        ) from exc

    context = omni.usd.get_context()
    stage = context.get_stage()
    if stage is None:
        context.new_stage()
        stage = context.get_stage()

    # Isaac Sim APIs vary by version. This file is a version-tolerant skeleton, not a brittle
    # one-shot scene generator. Adjust prim creation and robot import calls to your Isaac release.
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    scene_objects = [
        {"name": "plastic_bottle", "object_type": "trash", "position": [0.72, 0.14, 0.75]},
        {"name": "paper_wrapper", "object_type": "trash", "position": [0.84, -0.03, 0.74]},
        {"name": "paper_cup", "object_type": "trash", "position": [0.61, -0.18, 0.74]},
        {"name": "dustbin", "object_type": "container", "position": [1.05, -0.42, 0.19]},
        {"name": "red_hazard_zone", "object_type": "hazard", "position": [0.38, 0.64, 0.01]},
        {"name": "unitree_g1", "object_type": "robot", "position": [0.0, 0.0, 0.0]},
    ]

    _ensure_demo_environment(stage)
    _ensure_demo_lighting(stage)

    for spec in scene_objects:
        if spec["object_type"] == "robot":
            continue
        prim_path = f"/World/{spec['name']}"
        if not stage.GetPrimAtPath(prim_path):
            xform = UsdGeom.Xform.Define(stage, prim_path)
            translate = xform.AddTranslateOp()
            translate.Set(Gf.Vec3d(*spec["position"]))
        else:
            _set_xform(stage.GetPrimAtPath(prim_path), translate=spec["position"])

    _ensure_cylinder(
        stage,
        "/World/plastic_bottle/body",
        translate=(0.0, 0.0, 0.0),
        radius=0.035,
        height=0.22,
        color=(0.3, 0.76, 1.0),
    )
    _ensure_cube(
        stage,
        "/World/paper_wrapper/body",
        translate=(0.0, 0.0, 0.0),
        scale=(0.09, 0.05, 0.012),
        color=(0.96, 0.82, 0.38),
    )
    _ensure_cylinder(
        stage,
        "/World/paper_cup/body",
        translate=(0.0, 0.0, 0.0),
        radius=0.045,
        height=0.11,
        color=(0.92, 0.92, 0.95),
    )
    _ensure_cylinder(
        stage,
        "/World/dustbin/body",
        translate=(0.0, 0.0, 0.0),
        radius=0.12,
        height=0.38,
        color=(0.18, 0.8, 0.48),
    )
    _ensure_cylinder(
        stage,
        "/World/red_hazard_zone/body",
        translate=(0.0, 0.0, 0.0),
        radius=0.18,
        height=0.01,
        color=(0.92, 0.24, 0.24),
    )

    g1_prim_path = os.getenv("G1_ROBOT_PRIM", DEFAULT_G1_PRIM_PATH)
    g1_usd_path = _resolve_g1_usd_path()
    if g1_usd_path:
        if _spawn_g1_reference(stage, g1_prim_path, g1_usd_path):
            print(f"Referenced Unitree G1 asset at {g1_usd_path} -> {g1_prim_path}")
        else:
            print("Unable to reference Unitree G1 asset with the current Isaac Python environment.")
            _spawn_g1_placeholder(stage, g1_prim_path)
    else:
        print(
            "No Unitree G1 USD asset found via G1_USD_PATH / UNITREE_G1_USD_PATH / "
            "GROOTKEEPER_G1_USD. Creating a placeholder prim at /World/G1 instead."
        )
        _spawn_g1_placeholder(stage, g1_prim_path)

    _publish_scene_state_if_ros2_available(scene_objects)
    context.save_as_stage(DEMO_STAGE_PATH)
    print("Trashbot Isaac scene skeleton created with Unitree G1 as the target embodiment.")


if __name__ == "__main__":
    main()
