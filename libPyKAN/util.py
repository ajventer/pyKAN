#Shared Utility methods and classes
import sys
import json
import os
import glob
import errno
import hashlib
import multiprocessing
try:
    import requests
except ImportError:
    raise ImportError("This program requires the python3 requests module. Please install it using pip or your distro's package manager")

DEBUG = False
NOBAR = False

default_ckan_repo = "https://github.com/KSP-CKAN/CKAN-meta/archive/master.tar.gz"
repository_list = "https://raw.githubusercontent.com/KSP-CKAN/CKAN-meta/master/repositories.json"

def download_json(uri):
    debug ('Downloading %s' % uri)
    r = requests.get(uri)
    debug('Returning data: %s' % r.text)
    return r.json()

def shacheck(filename, sha, failonmissing=True):
    if not sha and failonmissing:
        return False
    if sha:
        if sha == '00000000':
            return True
        text = open(filename,'rb').read()
        if len(sha) == 40:
            hashobj = hashlib.sha1(text)
        else:
            hashobj = hashlib.sha256(text)
        if hashobj.hexdigest().upper() !=sha.upper():
            print('Error in sha verification of %s "%s" != "%s"' %(filename, hashobj.hexdigest().upper(), sha.upper()))
            return False
    return True

def __download_file__(dl_data):
    before = ''
    if dl_data['sha']:
        before = '%s_' % dl_data['sha'][:8]
    if dl_data['id']:
        before += '_%s' % dl_data['id']
    filename = dl_data['uri'].replace(':','').replace('/','_')
    filename = os.path.join(dl_data['cachedir'],'%s%s' %(before,filename))
    print("Filename: %s" %filename)
    retries = 0
    done = os.path.exists(filename) and shacheck(filename,dl_data['sha'])
    while not done and retries < dl_data['retries']:
        print('Downloading %s' % dl_data['uri'])
        try:
            r = requests.get(dl_data['uri'], stream=True)
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        if not NOBAR:
                            sys.stdout.write('#')
                        sys.stdout.flush()
                        f.write(chunk)
                done = True
            if r.status_code != 200:
                raise IOError("Download failed %s" %r.status_code)
            if shacheck(filename,dl_data['sha'], False):
                print()
                debug("Warning: Sha hash for %s does not match repo data" % filename)
        except Exception as e:
            retries += 1
            if retries >=  dl_data['retries']:
                raise
            debug ('Download error %s. %s  retries remain' %(e, dl_data['retries'] - retries))
            done = False
    print()
    if not dl_data['sha']:
        return filename
    else:
        return (filename,dl_data['sha'],dl_data['id'])

def download_files(urilist, cachedir, retries):
    dl_data = []
    for uri in urilist:
        dl_data.append({'id':'id' in uri and uri['id'] or '',"uri": uri['uri'],"cachedir": cachedir, 'retries': retries, 'sha': uri['sha']})
    pool = multiprocessing.Pool()
    return pool.map(__download_file__, dl_data)


def is_kspdir(path):
    return os.path.isdir(os.path.join(path,'GameData')) and os.path.join(path,'readme.txt') in glob.glob('%s/*' %path)

def error(message,code=1):
    sys.stderr.write('%s\n' %message)
    sys.exit(code)

def debug(message):
    if DEBUG:
        sys.stderr.write('%s\n' %message)
        sys.stderr.flush()

def debug_n(message):
    if DEBUG:
        sys.stderr.write('%s' %message)
        sys.stderr.flush()

def SaveJsonToFile(filename,data):
    open(filename,'w').write(json.dumps(data,indent=4))

def ReadJsonFromFile(filename, default=None,create=False):
    if default == None:
        return json.loads(str(open(filename).read()),strict=False)
    else:
        try:
            return ReadJsonFromFile(filename)
        except IOError:
            if create:
                SaveJsonToFile(filename,default)
            return default

def mkdir_p(targetpath):
    try:
        os.makedirs(targetpath)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return
