#Generic datatype for version information
from . import util
import re
from functools import total_ordering

@total_ordering
class Version(object):
    def __init__(self,*args,strict=True):
        """
        >>> Version('0.0.1').versionlist
        ['0', '0', '1']
        >>> Version((0,0,2)).versionlist
        ['0', '0', '2']
        >>> Version([0,0,3]).versionlist
        ['0', '0', '3']
        >>> Version(0,0,4).versionlist
        ['0', '0', '4']

        """
        self.strict = strict
        versionlist = []
        if len(args) == 1 and isinstance(args[0],str):
            vstring = args[0]
            if vstring.startswith('v') or vstring.startswith('V'):
                vstring = vstring[1:]
            versionlist = vstring.split('.')
        elif len(args) == 1:
            try:
            #If input is a list, tuple or other enumerable
                for c,i in enumerate(args[0]):
                    versionlist.append(i)
            except TypeError:
                #if it's not an enumerable we don't give up yet
                pass
        else:
            #We got the version as a series of arguments
            for i in args:
                versionlist.append(i)
        #It's best to have integers whenever possible
        self.versionlist = []
        for i in versionlist:
                #We need a common type for everything to get consistent comparisons
                #Strings are the most universal and numeric ones compare fairly well.
            i = str(i)
            #But extra leading zeroes screw things up
            while i.startswith('0') and len(i) > 1:
                i = i[1:]
            if i == '.':
                continue
            self.versionlist.append(i)

    def numpart(self,s):
        try:
            return int(''.join(re.findall('\d',s)))
        except ValueError:
            # if numpart is '', int() can't convert it so treat as 0
            return 0

    def __cmp__(self, other):
        """
        >>> Version(0,0,1) < Version(0,0,2)
        True
        >>> Version('0.0.2pre') < Version('0.0.2')
        True
        >>> Version(0,0,2) > Version(0,0,'2pre')
        True
        >>> Version('0.0.3') == Version([0,0,3])
        True
        >>> Version(0,0,4) == Version('0.0.4')
        True
        >>> Version(0,0,5,1) > Version(0,0,5)
        True
        >>> Version('0.4.3') < Version('0.14.3')
        True
        >>> Version('0.4.3', strict=True) != Version('0.4')
        True
        >>> Version('0.4.3', strict=False) == Version('0.4')
        True
        """
        if not isinstance(other,Version):
            other=Version(other)
        if self.versionlist == other.versionlist:
            #if the contents are identical it's a definite match
            return 0
        if not self.strict:
            #CKAN spec v1.16 ksp_version_strict compliance
            if self.versionlist[:-1] == other.versionlist:
                return 0
        if str(self) == 'any' or str(other) == 'any':
            return 0
        if len(other.versionlist) > len(self.versionlist):
            return -other.__cmp__(self)
        for c,i in enumerate(self.versionlist):
            try:
                j = other.versionlist[c]
            except IndexError:
                j = '0'
            if i == j:
                continue
            if re.findall('pre|alpha|beta',i):
                if self.numpart(i) <= self.numpart(j):
                    return -1
                else:
                    return 1
            if re.findall('pre|alpha|beta',j):
                if self.numpart(j) <= self.numpart(i):
                    return 1
                else:
                    return -1
            if i > j:
                return 1
            if i < j:
                return -1
        return 0

    def __lt__(self,other):
        return self.__cmp__(other) < 0

    def __eq__(self,other):
        return self.__cmp__(other) == 0

    def __str__(self):
        return '.'.join(self.versionlist)

    def __getitem__(self, key):
        return self.versionlist[key]

if __name__ == "__main__":
    import doctest
    doctest.testmod()
