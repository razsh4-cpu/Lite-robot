from glob import glob
from setuptools import find_packages, setup

package_name = "lite3_state_estimation"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml", "README.md"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="raz",
    maintainer_email="raz@localhost",
    description="Receive-only Lite3 high-level state bridge",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "high_level_state_bridge = lite3_state_estimation.high_level_state_bridge:main",
            "localization_guard = lite3_state_estimation.localization_guard:main",
        ],
    },
)
