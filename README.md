# pyKAN
PyKAN is a pure python alternative client for the CKAN utility to manage modules for Kerbal Space Program.
It uses the original upstream CKAN data and repos directly and does not fragment the module repositories,
it merely provides an alternate client to consume this data to manage, install and update modules.

All the logic is kept in libraries - so that writing a new interface is easy.

Version 0.0.1-pre

Installation:
  *Clone/Download the repository.
  *Change to the directory where you downloaded
  *./pykan --help

Current features:
  *Global settings holding list of known KSP installation directories
  *Per KSPDir settings on top of that

Todo:
  *Fetch repository data from CKAN
  *List available modules
  *Install modules (optional override support for manual mods) with optional download-retries
  *Delete modules
  *Upgrade modules
  *PyQT GUI for graphical usage



