#Class implementing all module management methods. Install, uninstall, upgrade.
from .installed import Installed
from .version import Version
from . import util
import sys
import os
import re
import zipfile
from .installed import Installed
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

class ConflictException(Exception):
    pass


class ModManager(object):
    def __init__(self, repoentries, settings, repo):
        self.repoentries = repoentries
        self.settings = settings
        self.repo = repo
        self.installed = Installed(self.settings, self.repo)

    def __get_sha__(self, repoentry):
        if not 'download_hash' in repoentry:
            return '00000000'
        if 'sha256' in repoentry['download_hash']:
            return repoentry['download_hash']['sha256']
        elif 'sha1' in repoentry['download_hash']:
            return repoentry['download_hash']['sha256']
        else:
            return None


    def download(self):
        util.debug(self.repoentries)
        urilist = [{'uri':i['download'],'sha':self.__get_sha__(i),'id':i['identifier']} for i in self.repoentries]
        util.debug('URILIST %s' % urilist)
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
        util.debug('MODFILES %s' %self.modfiles)
        for i in self.modfiles:
            mod = [m for m in self.repoentries if self.__get_sha__(m) == i[1] and m['identifier'] == i[2]][0]
            print("Installing module ",mod['identifier'])
            modfiles = []
            for target in mod.get('install',[{'PYKANBASIC':True,'install_to':'GameData'}]):
                #self.clear_the_way(find,self.dest(target['install_to']),'find_regexp' in target,target.get('find_matches_files',False))
                with zipfile.ZipFile(i[0],'r') as z:
                    for member in z.infolist():
                        util.debug('Zipfile Member: %s '%member.filename)
                        matched = False
                        if 'file' in target and target['file'] in member.filename:
                            matched = os.path.basename(member.filename)
                            mdir = member.filename
                            util.debug('Member directory: %s' %mdir)
                            util.debug('Basename: %s' %matched)
                            if 'GameData' in member.filename:
                                util.debug('Path contains GameData')
                                mlist = member.filename.split('/')
                                mpos = mlist.index('GameData')
                                mdir = '/'.join(mlist[mpos+1:])
                                util.debug('Extracted path: %s' %mdir)
                            if not mdir.endswith(matched):
                                util.debug('Partial path. Correcting')
                                matched = os.path.join(mdir,matched)
                            else:
                                matched = mdir
                        elif 'find' in target:
                            if '%s' %target['find'] in member.filename:
                                matched = os.path.basename(member.filename)
                                if 'GameData' in member.filename:
                                    mlist = member.filename.split('/')
                                    mpos = mlist.index('GameData')
                                    mdir = '/'.join(mlist[mpos+1:])
                                    if not mdir.endswith(matched):
                                        matched = os.path.join(mdir,matched)
                                    else:
                                        matched = mdir
                                else:
                                    matched = member.filename
                        elif 'find_regexp' in target:
                            r = re.findall(target['find_regexp'],member.filename)
                            if r:
                                mx = member.filename.split('/')
                                idx = mx.index(r[0])
                                matched = '/'.join(mx[idx:])
                        elif 'PYKANBASIC' in target:
                            #This actually means CKAN didn't give us any instructions
                            if 'GameData' in member.filename:
                                util.debug('Found GameData in file path')
                                #Sigh...really CKAN ? Really ?
                                mx = member.filename.split('/')
                                idx = mx.index('GameData') +1
                                matched = '/'.join(mx[idx:])
                            else:
                                matched = member.filename
                        else:
                            continue
                        if matched:
                            util.debug ('Match: %s'% matched)
                            endpoint = target.get('install_to','').split('/')[-1]
                            if endpoint == matched.split('/')[0]:
                                matched = '/'.join(matched.split('/')[1:])
                            dest = os.path.join(self.settings.KSPDIR,target.get('install_to',''),matched)
                            if member.filename.endswith('/'):
                                util.debug('Creating directory %s' % dest)
                                util.mkdir_p(dest)
                                modfiles.append(dest)
                            else:
                                #It sucks that the ZipFile.extract method can't do paths well enough
                                #so we are forced to do this.
                                if not os.path.exists(os.path.dirname(dest)):
                                    modfiles.append(os.path.dirname(dest))
                                    util.mkdir_p(os.path.dirname(dest))
                                util.debug('Extracting file %s' % dest)
                                open(dest,'wb').write(z.open(member).read())
                                modfiles.append(dest)
                self.installed.add_mod(mod['identifier'],mod,files=modfiles)

    def uninstall_list(self):
        ins = Installed(self.settings,self.repo)
        remlist = []
        for mod in self.repoentries:
            remlist.append(mod['identifier'])
        to_del = True
        while to_del:
            to_del = []
            for mod in remlist:
                for i in ins:
                    if i in remlist:
                        continue
                    for dep in ins[i].get('depends',[]):
                        if dep['name'] == mod:
                            to_del.append(i)
            remlist += to_del
        remlist = list(set(remlist))
        return remlist

    def remove(self, modname, deregister=True):
        print("Removing module %s" % modname)
        target = os.path.join(self.settings.KSPDIR,'GameData',modname)
        filelist = self.installed[modname].get('installed_files',[])
        if filelist:
            for file in filelist:
                util.debug('Removing %s' % file)
                if os.path.exists(file):
                    if os.path.isdir(file):
                        shutil.rmtree(file)
                    else:
                        os.unlink(file)
        if os.path.isdir(target):
            util.debug('Removing %s' % target)
            shutil.rmtree(target)
        if deregister:
            self.installed.remove_mod(modname)

    def upgrade(self):
        for mod in [i['identifier'] for i in self.repoentries]:
            self.remove(mod, False)
        self.get_download_list('no','no')
        self.download()
        self.install()


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
            for mod in list(dl_list.values()):
                if mod is None:
                    continue
                modconflicts = mod.get('conflicts',[])
                conflicts = modconflicts and [i.get('identifier','') for i in modconflicts if i in self.installed.all_modnames()] or []
                util.debug(conflicts)
                if conflicts:
                    raise ConflictException('Required mod %s conflicts with installed mod(s): %s' % (mod,','.join(conflicts)))
                for key in searchkeys:
                    if key in mod and mod[key] is not None:
                        thiskey = {}
                        for m in mod[key]:
                            if m['name'] in list(self.installed.all_modnames()):
                                continue
                            found =  self.repo.find_latest(m['name'])
                            if not found and key is  'depends': #Failing to find a suggestion is not a crisis
                                raise MissingDependencyException('Could not find module %s required by %s' %(m['name'],mod))
                            if len(found) > 1:
                                fnd = [i for i in found if i in dl_list or i in self.installed.all_modnames()]
                                if not fnd:
                                    raise MultiProviderException(','.join(list(found.keys())))
                                else:
                                    found = fnd
                            for f in found:
                                if f not in dl_list and f not in list(self.installed.all_modnames()) and not f in blacklist:
                                    thiskey[f] = found[f]
                        if thiskey and ((key == 'suggests' and suggests=='ask') or (key == 'recommends' and recommends =='ask')):
                            raise ConfirmException('%s:%s:%s' %(mod['identifier'],key,','.join(list(thiskey.keys()))))
                        to_add.update(thiskey)
            dl_list.update(to_add)
        # self.repoentries = []
        # for mod in dl_list:
        #     self.repoentries.append(mod)
        print()
        self.repoentries = []
        for mod in dl_list:
            self.repoentries.append(dl_list[mod])
        return dl_list
