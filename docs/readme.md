# Internal notes for azcam

## Docs
readthedocs - New documentation is deployed automatically by incoming webhook at https://azcam.readthedocs.io after a new push to github.

If not automatic then use "Build Version" on readthedocs project page.

mkdocs is used for local doc rendering with _build and _server commands 
 - writes html to **docs/site** root folder
 - mkdocs.yml defines mkdocs pars

mkdocstrings is used with mkdocs for autogenerated code docs

instance variables require docstring AFTER instance
 
# Misc
Use "flit publish" to update pypi and "pip install" or "pip install -e" to install azcam.