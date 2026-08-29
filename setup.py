from setuptools import find_packages, setup

setup(
    name="ix-hapticsight-ohip",
    version="0.2.0",
    description="Safety-first perception-to-contact authority for bounded robot and XR interaction.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Bryce Lovell",
    license="MIT",
    python_requires=">=3.10",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=["pyyaml>=6.0", "pillow>=10.0"],
    extras_require={"dev": ["pytest>=7.0"]},
    keywords=[
        "robotics",
        "computer-vision",
        "human-robot-interaction",
        "haptics",
        "safety",
        "ros2",
        "webxr",
        "protocol",
    ],
)
