# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name="alix-souverain-engine",
    version="1.0.0",
    author="Christian Duguay & Alix",
    description="Organisme souverain déterministe unifié — VERALUME × KAIROS V6",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "psutil>=5.9.0",
    ],
    extras_require={
        "sensory": ["Pillow>=10.0.0"],
    },
    entry_points={
        "console_scripts": [
            "alix=alix_engine.run_alix:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
