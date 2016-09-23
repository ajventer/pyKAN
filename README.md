# pyKAN
PyKAN is a pure python alternative client for the CKAN utility to manage modules for Kerbal Space Program.
It uses the original upstream CKAN data and repos directly and does not fragment the module repositories,
it merely provides an alternate client to consume this data to manage, install and update modules.

All the logic is kept in libraries - so that writing a new interface is easy.

Version 0.0.1-pre

##Installation:
1. Clone or Download the repository.
2. Change to the directory where you downloaded
3. ./pykan --help

##Current features:
1. Global settings holding list of known KSP installation directories
2. Per KSPDir settings on top of that

##Todo:
1. Fetch repository data from CKAN
2. List available modules
3. Install modules (optional override support for manual mods) with optional download-retries
4. Delete modules
5. Upgrade modules
6. PyQT GUI for graphical usage



