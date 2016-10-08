#Abstracts the list of installed modules.
from . import util
import os
from . import filters
import re
import glob
from .version import Version



class Installed(object):
    def __init__(self,settings,repo):
        self.settings = settings
        self.repo = repo
        self.cachedir = os.path.dirname(settings.KSPSettingsFile)
        self.installedListFile = os.path.join(self.cachedir,'installed_mods.json')
        self.installed_mods = util.ReadJsonFromFile(self.installedListFile, {'installed_modules':{},'manual_modules':{},'ckan_modules':{}}, True)

    def import_ckan(self):
        CKAN=os.path.join(self.settings.KSPDIR,'CKAN','registry.json')
        if os.path.exists(CKAN):
            CKANData = util.ReadJsonFromFile(CKAN)['installed_modules']
            for mod in CKANData:
                util.debug('Registering CKAN installed module %s' % mod)
                self.add_mod(mod,CKANData[mod]['source_module'],'ckan_modules',CKANData[mod]['installed_files'])


    def all_modnames(self):
        for i in ['installed_modules','manual_modules','ckan_modules']:
            for mod in self.installed_mods[i]:
                yield mod

    def __iter__(self):
        for k in ['installed_modules','manual_modules','ckan_modules']:
            for key in self.installed_mods[k]:
                yield key


    def __getitem__(self, key):
        for k in ['installed_modules','manual_modules','ckan_modules']:
            if key in self.installed_mods[k]:
                return self.installed_mods[k][key]
        raise KeyError

    def list_modules(self):
        for i in ['installed_modules','manual_modules','ckan_modules']:
            for mod in self.installed_mods[i]:
                yield {'identifier':mod, 'name': self.installed_mods[i][mod].get('name',''), 'version': self.installed_mods[i][mod]['version'],"status":self.modstatus(mod)}


    def modstatus(self,mod):
        if mod in self.installed_mods['installed_modules']:
            return 'Installed (PyKAN)'
        if mod in self.installed_mods['manual_modules']:
            return 'Installed (Manual)'
        if mod in self.installed_mods['ckan_modules']:
            return 'Installed (CKAN)'
        return 'Not installed'

    def add_mod(self,identifier,repoentry,subrepo='installed_modules',files=[]):
        self.installed_mods[subrepo][identifier] = repoentry
        if files:
            self.installed_mods[subrepo][identifier]['installed_files'] = files
        util.SaveJsonToFile(self.installedListFile, self.installed_mods)

    def remove_mod(self,identifier):
        for k in ['installed_modules','manual_modules','ckan_modules']:
            if identifier in self.installed_mods[k]:
                del(self.installed_mods[k][identifier])
        util.SaveJsonToFile(self.installedListFile, self.installed_mods)



    def get_manual_mods(self):
        self.installed_mods['manual_modules'] = {}
        util.debug('Searching for manually installed mods')
        names_found = {}
        striplen = len(self.settings.KSPDIR.split('/'))
        pathlist = self.repo.list_install_paths()
        for root, subdirs, files in os.walk(self.settings.KSPDIR):
            for f in files:
                fp = os.path.join(root,f)
                if 'Squad' in fp:
                    continue                
                fp = '/'.join(fp.split('/')[striplen:])
                if fp in pathlist:
                    names_found[pathlist[fp]] = {'path':fp}
            for s in subdirs:
                sp = os.path.join(root, s)
                if 'Squad' in sp:
                    continue                
                sp = '/'.join(sp.split('/')[striplen:])
                if sp.startswith('PYKAN') or sp.startswith('CKAN') or sp.endswith('GameData'):
                    continue
                if sp in pathlist:
                    names_found[pathlist[sp]] = {'path':sp}
                #Would be nice to make a version of this work - but we aren't there now.
                # else:
                #     possible = list(self.repo.list_modules([filters.Filter(self.settings).regex],{"needle": '%s' %os.path.basename(sp)}))
                #     if possible:
                #         names_found[possible[0]['identifier']] = {'path':sp}
                #         break
        #At this stage names_found should map every module we found to the paths we found it by.
        #Due to the ordering above, module directories take precedence over module files.
        #Now we need to try and determine the versions so we can match them to the correct repo entries.
        for name in sorted(names_found):
            #Skip anything that's already in our own dataset
            if not name in list(self.all_modnames()):
                util.debug('Trying to find version for %s' % name)
                path = os.path.join(self.settings.KSPDIR,names_found[name]['path'])
                util.debug('Found at %s' % path)
                if os.path.isfile(path):
                    util.debug('%s is a file' % path)
                    filename_search = re.findall('(\d+\.\d+\.\d*)',os.path.basename(names_found[name]['path']))
                    if filename_search:
                        util.debug('Regex version search found %s' %filename_search)
                        names_found[name]['version'] = filename_search[0]
                        util.debug(names_found[name])
                elif os.path.isdir(path):
                    vdata = None
                    util.debug('%s is a directory' %path)
                    for vfile in glob.iglob('%s/*.version' % path):
                        util.debug('Trying version file %s' % vfile)
                        tvdata = util.ReadJsonFromFile(vfile)
                        util.debug(tvdata)
                        if tvdata['NAME'] == name:
                            vdata = tvdata
                    if not vdata:
                        continue
                    names_found[name]['version'] = str(Version(vdata['VERSION']['MAJOR'],vdata['VERSION']['MINOR'],vdata['VERSION']['PATCH'],vdata['VERSION']['BUILD']))
                    util.debug(names_found[name])
                else:
                    continue
            else:
                util.debug('%s already in records' %name)
        util.debug (names_found)
        for name in [i for i in names_found if 'version' in names_found[i]]:
            util.debug(names_found[name])
            matches = [self.repo.repodata[i] for i in self.repo.repodata if self.repo.repodata[i]['identifier'] == name and Version(self.repo.repodata[i]['version']) == Version(names_found[name]['version'])]
            util.debug(matches)
            if matches:
                self.add_mod(name, matches[0],'manual_modules')
        














        


