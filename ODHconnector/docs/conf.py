"""Sphinx configuration."""
import os
import sys
import pathlib
project = 'MinervaS‑ODH Connector'
author = 'Elettra Palmisano & Gennaro Francesco Landi'
release = '0.1.0'
copyright = ''
# path setup
sys.path.insert(0, os.path.abspath('../src'))
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "myst_parser",
]
napoleon_google_docstring = True
napoleon_numpy_docstring = False
templates_path = ['_templates']
exclude_patterns = []
html_theme = 'sphinx_rtd_theme'
html_title = f"{project} · v{release}"

# --------------------------------------------------
# dynamic "today" substitution used in README
# --------------------------------------------------
from datetime import date
rst_epilog = f"""
.. |today| replace:: {date.today()}
"""

# enable substitutions inside Markdown
myst_enable_extensions = ["substitution", "colon_fence"]

# generate id/anchors for the first 3 heading levels ⇒
#   i.e.  ## Features  →  slug '#features'
myst_heading_anchors = 3
