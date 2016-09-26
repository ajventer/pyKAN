import util
import json
import os
import glob
import tarfile
import glob
from installed import Installed
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
        self.read_repository_data()
        ins = Installed(self.settings,self)
        ins.import_ckan()
        ins.get_manual_mods()


    def read_repository_data(self):
        self.cachedir=os.path.join(self.settings.KSPDIR,'PYKAN','repodata')
        util.mkdir_p(self.cachedir)
        if not len(glob.glob(self.cachedir+'/*')):
            self.update_repository_data()
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

    def install_path(self,repoentry):
        result = []
        for i in repoentry.get('install',[]):
            #Seriously CKAN ? different keys that this value may be in - and no difference between them ?
            for k in ['file','find']:
                f = i.get(k,'')
                f =os.path.join(i.get('install_to'),f)
                if f and f != 'GameData':
                    result.append(f)
        return list(set(result))


    def list_install_paths(self):
        result = {}
        if not self.repodata:
            self.read_repository_data()
        for i in self.repodata:
            for x in self.install_path(self.repodata[i]):
                result[x] = self.repodata[i].get('name')
        return result

    def list_modules(self,filtermethods=[],filterargs=[]):
        """
        List the modules in the repo, optionally filtering. filter should be a Filter class method. Parameters for the method afterwards
        """
        if not self.repodata:
            self.read_repository_data()
        for i in self.repodata:
            if not filtermethods:
                yield self.repodata[i]
            else:
                valid=True
                for f in filtermethods:
                    util.debug_n('%s,%s | %s' %(f,filterargs,self.repodata[i]))
                    if not f(self.repodata[i],**filterargs):
                        util.debug('-- False')
                        valid=False
                        break
                if valid:
                    yield self.repodata[i]


if __name__ == "__main__":
    import doctest
    doctest.testmod()


