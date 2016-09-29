#Class implementing all module management methods. Install, uninstall, upgrade.
from installed import Installed
from version import Version
import util

class MultiProviderException(Exception):
    pass    

class MissingDependencyException(Exception):
    pass    

class ModManager(object):
    def __init__(self, repoentries, settings, repo):
        self.repoentries = repoentries
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


    def get_download_list(self, recommends=True, suggests=False):
        #TODO - this algorithm is O(n*n) first thing we optimize after initial release.
        #There must be a faster way to do this. 
        #Paralelize maybe ? 
        dl_list = {}
        for mod in self.repoentries:
            dl_list[mod['identifier']] = mod
        searchkeys = ['depends']
        if recommends:
            searchkeys.append('recommends')
        if suggests:
            searchkeys.append('suggests')
        to_add = True
        count = 0
        while to_add:
            count += 1
            to_add = {}
            for mod in dl_list.values():
                for key in searchkeys:
                    if key in mod:
                        for m in mod[key]:
                            found =  self.repo.find_latest(m['name'])
                            if not found and key is not 'suggests': #Failing to find a suggestion is not a crisis
                                raise MissingDependencyException('Could not find module %s' %m['name'])
                            if len(found) > 1:
                                fnd = [i for i in found if i in dl_list or i in self.installed.all_modnames()]
                                if not fnd:
                                    raise MultiProviderException(','.join(found.keys()))
                                else:
                                    found = fnd
                            for f in found:
                                if f not in dl_list and f not in self.installed.all_modnames():
                                    to_add[f] = found[f]
            dl_list.update(to_add)
        # self.repoentries = []
        # for mod in dl_list:
        #     self.repoentries.append(mod)
        return dl_list


