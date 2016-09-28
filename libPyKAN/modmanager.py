#Class implementing all module management methods. Install, uninstall, upgrade.

class ModManager(object):
    def __init__(self, repoentry, settings, repo):
        self.repoentry = repoentry
        self.settings = settings
        self.repo = repo

    def __get_sha__(self, repoentry):
        if 'sha256' in repoentry['download_hash']:
            return repoentry['download_hash']['sha256']
        elif 'sha1' in repoentry['download_hash']:
            return repoentry['download_hash']['sha256']
        else:
            return None

    def get_download_list(self, reccomends=True, suggests=False):
        #This mod must always be in the list.
        dl_list = [{'uri': self.repoentry['download'], 'sha':self.__get_sha__(self.repoentry)}]
        #Dependencies always get added:
        
