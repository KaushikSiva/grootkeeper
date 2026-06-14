from setuptools import setup


package_name = "trashbot_bridge"


setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Grootkeeper",
    maintainer_email="you@example.com",
    description="ROS 2 bridge nodes for Grootkeeper Isaac Sim integration.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "groot_action_publisher=trashbot_bridge.groot_action_publisher:main",
            "isaac_execution_listener=trashbot_bridge.isaac_execution_listener:main",
            "scene_state_listener=trashbot_bridge.scene_state_listener:main",
        ]
    },
)
