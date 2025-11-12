# setup.py

from setuptools import find_packages, setup

# Read version from version.py
with open("dtmapi/version.py", "r") as f:
    exec(f.read())

setup(
    name="dtmapi",
    version=__version__,  # noqa: F821
    packages=find_packages(),
    install_requires=[
        "requests>=2.32.5",
        "pandas>=2.3.3",
        "openpyxl>=3.1.3",
    ],
    extras_require={
        "test": [
            "pytest>=9.0.0",
            "pytest-cov>=7.0.0",
            "pytest-mock>=3.15.1",
        ],
        "docs": [
            "sphinx>=8.0.0",
            "sphinx-rtd-theme>=3.0.2",
        ],
        "dev": [
            "ipykernel>=7.1.0",
        ],
    },
    description="A Python package for fetching data from the IOM's Displacement Tracking Matrix (DTM).",
    author="Luong Bang Tran",
    author_email="lutran@iom.int",
    license="MIT",
    url="https://github.com/Displacement-Tracking-Matrix/dtmapi",
    keywords=["dtm", "displacement", "tracking", "matrix", "iom", "idp", "humanitarian", "migration", "refugees"],
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    project_urls={
        "Github": "https://github.com/Displacement-Tracking-Matrix/dtmapi",
        "Documentation": "https://dtmapi.readthedocs.io/en/latest/",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Sociology",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
