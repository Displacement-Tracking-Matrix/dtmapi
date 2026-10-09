# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

# Read the version from the package, so the docs never fall behind a release.
_version_ns = {}
with open(os.path.join(os.path.dirname(__file__), "..", "dtmapi", "version.py")) as f:
    exec(f.read(), _version_ns)

project = "dtmapi"
copyright = "2025–2026, Displacement Tracking Matrix"
author = "Displacement Tracking Matrix"
release = _version_ns["__version__"]
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc",
]

# Show both the class docstring and __init__'s, so constructor parameters
# (api_version, environment, timeout, retries) appear in the reference.
autoclass_content = "both"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
