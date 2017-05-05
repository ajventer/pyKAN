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


    def modfiles(self, path):
        util.debug('Recording module data in %s' % path)
        if os.path.isfile(path):
            return [path]
        else:
            files = []
            for root,dirs,filelist in os.walk(path):
                files.append(root)
                for f in filelist:
                    util.debug('Adding %s '% f)
                    files.append(os.path.join(root,f))
        return files


    def get_manual_mods(self):
        self.installed_mods['manual_modules'] = {}
        util.debug('Searching for manually installed mods')
        names_found = {}
        striplen = len(self.settings.KSPDIR.split('/'))
        for item in glob.iglob('%s/*' % os.path.join(self.settings.KSPDIR,'GameData')):
            if os.path.basename(item) != 'Squad':
                names_found[os.path.basename(item)] =  {'path':item}
        for name in sorted(names_found):
            #Skip anything that's already in our own dataset
            if not name in list(self.all_modnames()):
                util.debug('Trying to find version for %s' % name)
                if os.path.isfile(names_found[name]['path']):
                    util.debug('%s is a file' % names_found[name]['path'])
                    filename_search = re.findall('(\d+\.\d+\.\d*)',os.path.basename(names_found[name]['path']))
                    if filename_search:
                        util.debug('Regex version search found %s' %filename_search)
                        newname = name.split(filename_search[0])[0]
                        for i in ['.','_','-']:
                            if newname.endswith(i):
                                newname = newname[:-1]
                        names_found[newname] = names_found[name]
                        names_found[newname]['version'] = Version(filename_search[0])
                        util.debug(names_found[newname])
                elif os.path.isdir(names_found[name]['path']):
                    util.debug('%s is a directory' %names_found[name]['path'])
                    for vfile in glob.iglob('%s/*.version' % names_found[name]['path']):
                        util.debug('Trying version file %s' % vfile)
                        try:
                            vdata = util.ReadJsonFromFile(vfile)
                        except:
                            continue
                        util.debug(vdata)
                        vstring = vdata['VERSION'].get('MAJOR')
                        for k in ['MINOR','PATCH','BUILD']:
                            v = vdata['VERSION'].get(k)
                            vstring = '%s%s' %(vstring,v is not None and '.%s'%v or '')
                        names_found[name]['version'] = Version(vstring)
                        util.debug(names_found[name])
                else:
                    continue
            else:
                util.debug('%s already in records' %name)
        util.debug (names_found)
        for name in [i for i in names_found if 'version' in names_found[i]]:
            util.debug('%s: %s' % (name, names_found[name]))
            matches = [self.repo.repodata[i] for i in self.repo.repodata if self.repo.repodata[i]['identifier'] == name and Version(self.repo.repodata[i]['version']) == names_found[name]['version']]
            util.debug('Matches: %s' % matches)
            if matches:
                self.add_mod(name, matches[0],'manual_modules',self.modfiles(names_found[name]['path']))
