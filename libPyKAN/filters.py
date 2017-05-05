#Class that implements various module list filters.
import re
from .version import Version

class Filter(object):
    def __init__(self,settings):
        self.settings = settings
        pass

    def compatible(self, repoentry, **kwargs):
        """
        >>> from pykancfg import PyKANSettings
        >>> f = Filter(PyKANSettings('test'))
        >>> f.compatible({"ksp_version":"1.0.0"})
        True
        >>> f.compatible({"ksp_version": "1.2.0"})
        False
        >>> f.compatible({"ksp_version_min": "1.2.0"})
        False
        >>> f.compatible({"ksp_version_min": "1.0.0"})
        True
        >>> f.compatible({"ksp_version_min": "0.2.0"})
        True
        >>> f.compatible({"ksp_version_max": "1.0.0"})
        True
        >>> f.compatible({"ksp_version_max": "1.2.0"})
        True
        >>> f.compatible({"ksp_version_max": "0.2.0"})
        False
        """
        modversion = repoentry.get('ksp_version',None)
        if modversion:
            return modversion == 'any' or Version(modversion) >= Version(self.settings.KSPSettings['minKSPversion']) and Version(modversion) <= Version(self.settings.KSPSettings['maxKSPversion'])
        minversion = repoentry.get('ksp_version_min',None)
        maxversion = repoentry.get('ksp_version_max',None)
        if minversion and not maxversion:
            return  Version(self.settings.KSPSettings['maxKSPversion']) >= Version(minversion)
        if maxversion and not minversion:
            return Version(self.settings.KSPSettings['minKSPversion']) <= Version(maxversion)
        if minversion and maxversion:
            return Version(self.settings.KSPSettings['maxKSPversion']) >= Version(minversion) and Version(self.settings.KSPSettings['minKSPversion']) <= Version(maxversion)

        #If we can't figure out compatibility - we assume yes. My first thought would be no but apparently CKAN assumes yes - which forces us to follow suit
        return True




    def regex(self,repoentry,**kwargs):
        """
        >>> from pykancfg import PyKANSettings
        >>> f = Filter(PyKANSettings('test'))
        >>> f.regex({"name":"powermetal"},needle='met')
        True
        >>> f.regex({"name":"powermetal"},needle='foo')
        False
        """
        needle = kwargs['needle']
        result = []
        for k in repoentry:
            try:
                result += re.findall(needle,str(repoentry[k]),re.IGNORECASE) #pylint: disable=E1101
            except:
                continue
        return len(result) > 0

    def for_ksp_version(self,repoentry,**kwargs):
        """
        >>> from pykancfg import PyKANSettings
        >>> f = Filter(PyKANSettings('test'))
        >>> f.for_ksp_version({"ksp_version":"1.0.2"},kspversion="1.0.2")
        True
        >>> f.for_ksp_version({"ksp_version":"1.0.2"},kspversion="1.0.1")
        False
        """
        modversion = repoentry.get('ksp_version','')
        minversion = repoentry.get('ksp_version_min','')
        maxversion = repoentry.get('ksp_version_max','')
        kspversion = kwargs['kspversion']
        if modversion:
            return Version(modversion) == Version(kspversion)
        if minversion and not maxversion:
            return Version(kspversion) >= Version(minversion)
        if maxversion and not minversion:
            return Version(kspversion) <= Version(maxversion)
        if maxversion and minversion:
            return Version(kspversion) >= Version(minversion) and Version(kspversion) <= Version(maxversion)


    def by_mod_version(self,repoentry, **kwargs):
        """
        >>> from pykancfg import PyKANSettings
        >>> f = Filter(PyKANSettings('test'))
        >>> f.by_mod_version({"version":"1.0"},compareversion="1.0")
        True
        """
        compareversion = kwargs['compareversion']
        return Version(compareversion) == Version(repoentry.get('version','-1'))



if __name__ == "__main__":
    import doctest
    doctest.testmod()
