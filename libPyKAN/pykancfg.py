#Manages and provides access to the pykan specific settings files.
#To files are kept. One in $HOME/.pykan.json which stores the paths to
#all registered KSP installs. One in each KSPDIR/PYKAN/pykan_settings.json 
#which stores all other settings specific to each install.

import json
import os
import util
import copy

class PyKANSettings(object):
    def __init__(self, KSPDIR=None):
        self.SharedSettingsFile = os.path.join(os.getenv('HOME'),'.pykan.json')
        self.SharedSettings = {'KSPDIRS': [],"DownLoadRetryMax": 1}
        steamKSPDir = os.path.join(os.getenv('HOME'),'.steam','steamapps','common','Kerbal Space Program')
        if util.is_kspdir(steamKSPDir):
            self.SharedSettings['KSPDIRS'].append(steamKSPDir)
        self.SharedSettings = util.ReadJsonFromFile(self.SharedSettingsFile, self.SharedSettings, create=True)
        self.KSPSettings={'Repos':[util.default_ckan_repo]}
        if not KSPDIR and len(self.SharedSettings['KSPDIRS']):
            KSPDIR=self.SharedSettings['KSPDIRS'][0]
        if KSPDIR and KSPDIR in self.SharedSettings.get('KSPDIRS',[]):
            self.KSPSettingsFile = os.path.join(KSPDIR,'PYKAN','pykan_settings.json')
            util.mkdir_p(os.path.dirname(self.KSPSettingsFile))
            self.KSPSettings=util.ReadJsonFromFile(self.KSPSettingsFile,self.KSPSettings,create=True)
        elif KSPDIR:
            self.KSPSettingsFile = os.path.join(KSPDIR,'PYKAN','pykan_settings.json')

        util.debug('Settings object initated: %s' % self.view_all())
        self.KSPDIR=KSPDIR

    def __allsettings__(self):
        Settings=copy.deepcopy(self.SharedSettings)
        Settings.update(self.KSPSettings)
        return Settings

    def view_all(self):
        return json.dumps(self.__allsettings__(),indent=4)

    def flatsettings(self):
        settings = {}
        for k, v in self.__allsettings__().items():
            if not isinstance(v, list) or isinstance(v, dict):
                settings[k] = v
        return settings

    def reload(self):
        self.__init__(self.KSPDIR)

    def save(self):
        util.SaveJsonToFile(self.SharedSettingsFile,self.SharedSettings)
        util.SaveJsonToFile(self.KSPSettingsFile,self.KSPSettings)

    def addkspdir(self,kspdir):
        util.debug('Added %s to KSPDIRS and set to default')
        self.SharedSettings['KSPDIRS'].insert(0,kspdir)
        self.SharedSettings['KSPDIRS'] = list(set(self.SharedSettings['KSPDIRS']))
        self.save()

    def delkspdir(self,kspdir):
        util.debug('Deleting %s from KSPDIRS' %kspdir)
        idx = self.SharedSettings['KSPDIRS'].index(kspdir)
        del(self.SharedSettings['KSPDIRS'][idx])
        self.save()

    def setdefaultksp(self,kspdir):
        self.addkspdir(kspdir) #Since the default is first on the list and new items are always added 0 and we don't store duplicates :)

    def repos(self):
        return self.KSPSettings['Repos']

    def __str__(self):
        return json.dumps(self.flatsettings(),indent=4)

    def __getitem__(self,key):
        if key in self.SharedSettings:
            util.debug('Found %s in shared settings' % key)
            return self.SharedSettings[key]
        if key in self.KSPSettings:
            util.debug('Found %s in install specific settings' % key)
            return self.KSPSettings[key]
        util.debug('Could not find %s' % key)
        raise ItemError

    def __setitem__(self,key, value):
        util.debug('Setting key %s to %s' %(key,value))
        if key in self.SharedSettings:
            util.debug('Found %s in shared settings' %key)
            self.SharedSettings[key] = value
        else:
            #Shared settings has a very limited data set - all other keys are install specific
            util.debug('Updating %s in KSPDir settings' % key)
            self.KSPSettings[key] = value

    def set(self, key, value):
        #The setitem magic method isn't working as advertised for some bizarre reason
        #this provides a work-around until I can figure out why.
        self.__setitem__(key, value)

    def __iter__(self):
        for k in self.__allsettings__():
            yield (k)

    def items(self):
        for k,v in self.__allsettings__().items():
            yield (k,v)

    def __contains__(self, item):
        return item in self.SharedSettings or item in self.KSPSettings

    def __len__(self):
        return len(list(self.SharedSettings.keys())) + len(list(self.KSPSettings.keys()))













