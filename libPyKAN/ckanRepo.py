import util
import json
import os
import glob

class CkanRepo(object):
    def __init__(self,settings):
        self.settings = settings
        self.repodata = self.read_repository_data()


    def available_repo_list(self):
        RepoListFile = os.path.join(self.settings.KSPDIR,'PYKAN','repolist.json')
        if not os.path.isfile(RepoListFile):
            util.SaveJsonToFile(RepoListFile,util.download_json(util.repository_list))
        return util.ReadJsonFromFile(RepoListFile)['repositories']

    def update_repository_data(self):
        repofiles = util.download_files(self.settings.repos(), 
            self.cachedir, 
            self.settings['DownLoadRetryMax'])
        #Need to add file extraction code here

    def read_repository_data(self):
        self.cachedir=os.path.join(self.settings.KSPDIR,'PYKAN','repodata')
        util.mkdir_p(self.cachedir)
        #Need to finish writing this method
        return {}




