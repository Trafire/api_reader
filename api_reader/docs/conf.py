"""Sphinx configuration."""
project = "Api_Reader"
author = "Antoine Wood"
copyright = "2023, Antoine Wood"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
