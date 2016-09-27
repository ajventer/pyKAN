#Abstracts the list of installed modules.
import util
import os
import filters
import re
import glob
from version import Version



class Installed(object):
    def __init__(self,settings,repo):
        self.settings = settings
        self.repo = repo
        self.cachedir = os.path.dirname(settings.KSPSettingsFile)
        self.installedListFile = os.path.join(self.cachedir,'installed_mods.json')
        self.installed_mods = util.ReadJsonFromFile(self.installedListFile, {}, True)

    def import_ckan(self):
        #TODO implement this
        pass

    def add_mod(self,name,repoentry):
        self.installed_mods[name] = repoentry
        util.SaveJsonToFile(self.installedListFile, self.installed_mods)

    def get_manual_mods(self):
        util.debug('Searching for manually installed mods')
        names_found = {}
        striplen = len(self.settings.KSPDIR.split('/'))
        pathlist = self.repo.list_install_paths()
        for root, subdirs, files in os.walk(self.settings.KSPDIR):
            for f in files:
                fp = os.path.join(root,f)
                fp = '/'.join(fp.split('/')[striplen:])
                if fp in pathlist:
                    names_found[pathlist[fp]] = {'path':fp}
            for s in subdirs:
                sp = os.path.join(root, s)
                sp = '/'.join(sp.split('/')[striplen:])
                if sp.startswith('PYKAN') or sp.startswith('CKAN') or sp.endswith('GameData'):
                    continue
                if sp in pathlist:
                    names_found[pathlist[sp]] = {'path':sp}
                else:
                    possible = list(self.repo.list_modules([filters.Filter(self.settings).regex],{"needle": '%s' %os.path.basename(sp)}))
                    if possible:
                        names_found[possible[0]['name']] = {'path':sp}
                        break
        #At this stage names_found should map every module we found to the paths we found it by.
        #Due to the ordering above, module directories take precedence over module files.
        #Now we need to try and determine the versions so we can match them to the correct repo entries.
        for name in sorted(names_found):
            #Skip anything that's already in our own dataset
            if not name in self.installed_mods:
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
            matches = [self.repo.repodata[i] for i in self.repo.repodata if self.repo.repodata[i].get('name') == name and self.repo.repodata[i]['version'] == names_found[name]['version']]
            util.debug(matches)
            if matches:
                self.add_mod(name, matches[0])
        














        


