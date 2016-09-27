# pyKAN
PyKAN is a pure python alternative client for the CKAN utility to manage modules for Kerbal Space Program.
It uses the original upstream CKAN data and repos directly and does not fragment the module repositories,
it merely provides an alternate client to consume this data to manage, install and update modules.

All the logic is kept in libraries - so that writing a new interface is easy.

Version 0.0.1-pre

##Installation:
1. Clone or Download the repository.
2. Change to the directory where you downloaded
3. `./pyKAN --help`

##Current features:
1. Global settings holding list of known KSP installation directories
2. Per KSPDir settings on top of that
3. Fetch repository data from CKAN
4. Ability to install incompatible mods. Settings contain minKSPversion and maxKSPversion per install. By default these are set to the KSP version. User can override to, for example, allow mods that are maxed at 1.0.0 to install in 1.1.0.
5. List available modules. Module listing comes with numerous optional filters which can be combined in arbitrary combinations. Includes text-search, module version and KSP version compatibility. The same filters will be available for selecting mods to install.
6. Detect manually installed mods
7. Import list of modules installed by CKAN
8. List installed modules, indicating how they were installed. 

##Todo:
1. Install modules (optional override support for manual mods) with optional download-retries
2. Uninstall modules
3. Upgrade modules
4. PyQT GUI for graphical usage
5. Manual install by link. User can copy a download link and have the app download and install from within. User could add/edit mod information.



