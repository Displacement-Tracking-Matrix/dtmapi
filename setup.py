# setup.py

from setuptools import find_packages, setup

setup(
    name="dtmapi",
    version="0.0.9",
    packages=find_packages(),
    install_requires=["requests", "pandas"],
    description="A Python package for fetching data from the IOM's Displacement Tracking Matrix (DTM).",
    author="Luong Bang Tran",
    author_email="lutran@iom.int",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    project_urls={
        "Github": "https://github.com/Displacement-Tracking-Matrix/dtmapi",
        "Documentation": "https://pydtm.readthedocs.io/en/latest/",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
