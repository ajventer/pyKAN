# pyKAN
PyKAN is a pure python alternative client for the CKAN utility to manage modules for Kerbal Space Program.
It uses the original upstream CKAN data and repos directly and does not fragment the module repositories,
it merely provides an alternate client to consume this data to manage, install and update modules.

All the logic is kept in libraries - so that writing a new interface is easy.

Version 0.0.1-pre

##Installation:
1. Clone or Download the repository.
2. Change to the directory where you downloaded
3. ./pyKAN --help

##Current features:
1. Global settings holding list of known KSP installation directories
2. Per KSPDir settings on top of that
3. Fetch repository data from CKAN

##Todo:
1. List available modules
2. Install modules (optional override support for manual mods) with optional download-retries
3. Delete modules
4. Upgrade modules
5. PyQT GUI for graphical usage



