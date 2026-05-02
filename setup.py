"""
Server Test Framework - Package Setup

Entry points for pytest plugin discovery and layer registration.
"""

from setuptools import setup, find_packages


setup(
    name="server-test-framework",
    version="0.1.0",
    description="Layered server testing framework with plugin extensibility",
    author="Server Test Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pytest>=7.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-xdist>=3.0.0",
            "pytest-cov>=4.0.0",
        ],
        "ipmi": [
            "python-ipmi>=0.4.0",
        ],
        "redfish": [
            "redfish_utilities>=3.0.0",
        ],
    },
    entry_points={
        "server_test_plugins": [
            "hardware = layers.hardware:HardwareLayer",
            "component = layers.component:ComponentLayer",
            "bmc = layers.bmc:BMCLayer",
        ],
        "console_scripts": [
            "server-test=cli:main",
        ],
        "pytest11": [
            "server_test_framework=src.core.fixtures",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
