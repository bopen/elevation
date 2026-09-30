# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Import and path setup ---------------------------------------------------

import importlib.metadata

# -- Project information -----------------------------------------------------

project = "elevation"
copyright = "2016-2026 B-Open Solutions srl"
author = "B-Open Solutions srl"
release = importlib.metadata.version("elevation")
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    "autoapi.extension",
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

# autodoc configuration
autodoc_typehints = "none"

# autoapi configuration
autoapi_add_toctree_entry = False
autoapi_dirs = ["../elevation"]
autoapi_ignore = ["*/version.py"]
autoapi_member_order = "groupwise"
autoapi_options = [
    "members",
    "inherited-members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
autoapi_root = "_api"

# napoleon configuration
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_preprocess_types = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The root toctree document.
root_doc = "index"

# The suffix(es) of source filenames, as a list of unique file suffixes.
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.
html_theme = "pydata_sphinx_theme"

# The base URL of the published documentation, used in the canonical URLs.
html_baseurl = "https://elevation.bopen.eu/"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
