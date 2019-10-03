from . import util
import json
import os
import glob
import tarfile
from .installed import Installed
from .filters import Filter
from .version import Version

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
        print("Downloading updated repositories")
        RepoListFile = os.path.join(self.settings.KSPDIR,'PYKAN','repolist.json')
        util.SaveJsonToFile(RepoListFile,util.download_json(util.repository_list))
        uris = []
        for i in self.settings.repos():
            uris.append({'uri': i, 'sha': None, 'id': None})
        repofiles = util.download_files(uris,
            self.cachedir,
            self.settings['DownLoadRetryMax'])
        print("Parsing repository contents")
        self.read_repository_data(True)
        ins = Installed(self.settings,self)
        print("Updating list of installed modules")
        ins.import_ckan()
        ins.get_manual_mods()

    def find_latest(self, identifier, filters=None, filterargs={}):
        if filters is None:
            filters = [Filter(self.settings).compatible]
        result = {}
        for i in self.list_modules(filters,filterargs):
            if (i['identifier'].lower() == identifier.lower() or
                i['name'].lower() == identifier.lower() or
                identifier.lower() in ( x.lower() for x in i.get('provides',[]))):
                if  i['identifier'] not in result or Version(i['version']) >= Version(result[i['identifier']]['version']):
                    result[i['identifier']] = i
        return result

    def find_version(self, identifier, version):
        for i in self.repodata:
            if (self.repodata[i]['identifier'].lower() == identifier.lower() or self.repodata[i]['name'].lower() == identifier.lower()) and Version(self.repodata[i]['version']) == Version(version):
                return self.repodata[i]
        return None

    def read_repository_data(self, rebuild=False):
        self.repofile = os.path.join(self.settings.KSPDIR,'PYKAN','repocache.json')
        self.cachedir=os.path.join(self.settings.KSPDIR,'PYKAN','repodata')
        if not rebuild:
            self.repodata = util.ReadJsonFromFile(self.repofile, {}, create=True)
            if not self.repodata:
                rebuild = True
        if rebuild:
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
                            entrydata = json.loads(str(tar.extractfile(tarinfo).read(),'utf-8'))
                            util.debug(json.dumps(entrydata, indent=4))
                            if not 'identifier' in entrydata:
                                if 'name' in entrydata:
                                    entrydata['identifier'] = entrydata['name']
                                else:
                                    continue
                            self.repodata[tarinfo.name] = entrydata
                        except ValueError:
                            #Not a json file ?
                            continue
                tar.close()
            util.SaveJsonToFile(self.repofile, self.repodata)

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
                result[x] = self.repodata[i]['identifier']
        return result

    def list_modules(self,filtermethods=[],filterargs={}):
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
                    if not f(self.repodata[i],**filterargs):
                        valid=False
                        break
                if valid:
                    yield self.repodata[i]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
