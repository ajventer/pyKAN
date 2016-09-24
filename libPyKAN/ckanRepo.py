import util
import json
import os
import glob
import tarfile
import glob

class CkanRepo(object):
    def __init__(self,settings):
        """
        >>> import pykancfg
        >>> c = CkanRepo(pykancfg.PyKANSettings('test'))
        >>> c.update_repository_data()
        >>> c.read_repository_data()
        >>> isinstance(c.repodata, dict)
        True
        """
        self.settings = settings
        self.repodata = {}
        if self.settings.KSPDIR:
            self.read_repository_data()


    def available_repo_list(self):
        RepoListFile = os.path.join(self.settings.KSPDIR,'PYKAN','repolist.json')
        if not os.path.isfile(RepoListFile):
            util.SaveJsonToFile(RepoListFile,util.download_json(util.repository_list))
        return util.ReadJsonFromFile(RepoListFile)['repositories']

    def update_repository_data(self):
        RepoListFile = os.path.join(self.settings.KSPDIR,'PYKAN','repolist.json')
        util.SaveJsonToFile(RepoListFile,util.download_json(util.repository_list))
        repofiles = util.download_files(self.settings.repos(), 
            self.cachedir, 
            self.settings['DownLoadRetryMax'])
        #Need to add file extraction code here

    def read_repository_data(self):
        self.cachedir=os.path.join(self.settings.KSPDIR,'PYKAN','repodata')
        util.mkdir_p(self.cachedir)
        for repofile in glob.iglob(self.cachedir+'/*'):
            util.debug('Reading %s' % repofile)
            if not tarfile.is_tarfile (repofile):
                util.debug('%s is not a tarfile -skipping' % repofile)
                continue
            tar = tarfile.open(repofile,'r:*')
            for tarinfo in tar:
                util.debug("%s | %s" %(tarinfo.name,tarinfo.isreg() and 'file' or tarinfo.isdir() and'directory' or 'other'))
                if tarinfo.isreg():
                    try:
                        entrydata = json.loads(tar.extractfile(tarinfo).read())
                        util.debug(json.dumps(entrydata, indent=4))
                        self.repodata[tarinfo.name] = entrydata
                    except ValueError:
                        #Not a json file ?
                        continue
            tar.close()

    def listmodules(filter=None,filtervalue=None):
        pass

if __name__ == "__main__":
    import doctest
    doctest.testmod()


