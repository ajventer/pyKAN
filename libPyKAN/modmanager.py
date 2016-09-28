#Class implementing all module management methods. Install, uninstall, upgrade.
from installed import Installed
from version import Version
import util

class ModManager(object):
    def __init__(self, repoentry, settings, repo):
        self.repoentry = repoentry
        self.settings = settings
        self.repo = repo
        self.installed = Installed(self.settings, self.repo)

    def __get_sha__(self, repoentry):
        if 'sha256' in repoentry['download_hash']:
            return repoentry['download_hash']['sha256']
        elif 'sha1' in repoentry['download_hash']:
            return repoentry['download_hash']['sha256']
        else:
            return None

    def __deplist__(self, key, has=[]):
        result = []
        insmods = list(self.installed.all_modnames())
        if self.repoentry in has:
            return []
        if key in self.repoentry:
            for mod in self.repoentry[key]:
                mod = mod['name']
                m = self.repo.find_latest(mod)
                if not m:
                    util.error('Could not find required dependency %s' % mod)
                if m['identifier'] in insmods or m.get('name','') in insmods:
                    try:
                        imod = self.installed.installed_mods[m['identifier']]
                    except KeyError:
                        imod = self.installed.installed_mods[m['name']]
                    if Version(m['version']) <= Version(imod['version']):
                        continue #Better version already installed
                result.append(m)
                result += ModManager(m,self.settings, self.repo).__deplist__(key, result)
        return result
                

    def get_download_list(self, recommends=True, suggests=False):
        #This mod must always be in the list.
        dl_list = [{'uri': self.repoentry['download'], 'sha':self.__get_sha__(self.repoentry)}]
        #Dependencies always get added:
        for mod in self.__deplist__('depends'):
            dl_list.append({'uri': mod['download'], 'sha': self.__get_sha__(mod)})
        if recommends:           
            for mod in self.__deplist__('recommends'):
                dl_list.append({'uri': mod['download'], 'sha': self.__get_sha__(mod)})
        if suggests:
            for mod in self.__deplist__('suggests'):
                dl_list.append({'uri': mod['download'], 'sha': self.__get_sha__(mod)})
        return dl_list


