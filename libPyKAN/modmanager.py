#Class implementing all module management methods. Install, uninstall, upgrade.
from installed import Installed
from version import Version
import util
import sys
import os
import re
import zipfile
import shutil #Warning to windows porters - not sure how well this works on windows

#These exceptions are used as callbacks to alert calling applications that we need human input
#This way the handling of input is kept out of the library and so the same code will work
#unalterated for the QT version as is used by the commandline version.
class MultiProviderException(Exception):
    pass    

class MissingDependencyException(Exception):
    pass

class ConfirmException(Exception):
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


    def download(self):
        urilist = [{'uri':i['download'],'sha':self.__get_sha__(i)} for i in self.repoentries]
        util.debug(urilist)
        self.cachedir = os.path.join(self.settings.KSPDIR,'PYKAN','cache')
        util.mkdir_p(self.cachedir)
        self.modfiles = util.download_files(urilist,self.cachedir,self.settings['DownLoadRetryMax'])
        return self.modfiles


    def clear_the_way(self,find,install_to,is_regex=False, matches_files=False):
        for root,dirs,files in os.walk(install_to):
            if not matches_files:
                for d in dirs:
                    dname = os.path.join(root,d)
                    if d == find or is_regex and re.findall(find,dname):
                            util.debug('Clearing directory %s' % dname)
                            shutil.rmtree(dname)
            else:
                for f in files:
                    fname = os.path.join(root,f)
                    if f == find or is_regex and re.findall(find,fname):
                        util.debug('Clearing file %s' % fname)
                        os.unlink(fname)        


    def install(self):
        modlist = {}
        for i in self.modfiles:
            mod = [m for m in self.repoentries if self.__get_sha__(m) == i[1]][0]
            print "Installing module ",mod['identifier']
            for target in mod['install']:
                #self.clear_the_way(find,self.dest(target['install_to']),'find_regexp' in target,target.get('find_matches_files',False))
                with zipfile.ZipFile(i[0],'r') as z:
                    for member in z.infolist():
                        util.debug(member.filename)
                        matched = False
                        if 'file' in target and member.filename.endswith(target['file']):
                           matched = os.path.basename(member.filename)
                        elif 'find' in target:
                            if target.get('find_matches_files', False):
                                if member.filename.endswith(target['find']):
                                    matched = target['find']
                            else:
                                if '/%s/' %target['find'] in member.filename:
                                    mx = member.filename.split('/')
                                    idx = mx.index(target['find'])
                                    matched = '/'.join(mx[idx:])
                        elif 'find_regexp' in target:
                            r = re.findall(target['find_regexp'],member.filename)
                            if r:
                                mx = member.filename.split('/')
                                idx = mx.index(r[0])
                                matched = '/'.join(mx[idx:])   
                        else:
                            continue
                        if matched:
                            dest = os.path.join(self.settings.KSPDIR,target.get('install_to',''),matched)
                            if member.filename.endswith('/'):
                                util.debug('Creatinf directory %s' % dest)
                                util.mkdir_p(dest)
                            else:
                                #It sucks that the ZipFile.extract method can't do paths well enough
                                #so we are forced to do this.
                                util.debug('Extracting file %s' % dest)
                                open(dest,'w').write(z.open(member).read())


    def get_download_list(self, recommends='ask', suggests='ask',blacklist=[]):
        #TODO - this algorithm is O(n^2 +1) first thing we optimize after initial release.
        #There must be a faster way to do this. 
        #Paralelize maybe ? 
        dl_list = {}
        for mod in self.repoentries:
            dl_list[mod['identifier']] = mod
        searchkeys = ['depends']
        if recommends in ['yes','ask']:
            searchkeys.append('recommends')
        if suggests in ['yes','ask']:
            searchkeys.append('suggests')
        to_add = True
        count = 0
        while to_add:
            count += 1
            to_add = {}
            for mod in dl_list.values():
                for key in searchkeys:
                    if key in mod:
                        thiskey = {}
                        for m in mod[key]:
                            sys.stdout.write('.')
                            sys.stdout.flush()
                            found =  self.repo.find_latest(m['name'])
                            if not found and key is  'depends': #Failing to find a suggestion is not a crisis
                                raise MissingDependencyException('Could not find module %s required by %s' %(m['name'],mod))
                            if len(found) > 1:
                                fnd = [i for i in found if i in dl_list or i in self.installed.all_modnames()]
                                if not fnd:
                                    raise MultiProviderException(','.join(found.keys()))
                                else:
                                    found = fnd
                            for f in found:
                                if f not in dl_list and f not in self.installed.all_modnames() and not f in blacklist:
                                    thiskey[f] = found[f]
                        if thiskey and ((key == 'suggests' and suggests=='ask') or (key == 'recommends' and recommends =='ask')):
                            raise ConfirmException('%s:%s:%s' %(mod['identifier'],key,','.join(thiskey.keys())))
                        to_add.update(thiskey)
            dl_list.update(to_add)
        # self.repoentries = []
        # for mod in dl_list:
        #     self.repoentries.append(mod)
        print
        self.repoentries = []
        for mod in dl_list:
            self.repoentries.append(dl_list[mod])
        return dl_list


