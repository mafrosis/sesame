from __future__ import absolute_import

import codecs
import collections
import contextlib
import errno
import fnmatch
import json
import os
import shutil
import tempfile

from keyczar.keys import AesKey

from . import SesameError
from . import MODE_ENCRYPT, MODE_DECRYPT


def get_keys(args):
    """
    Get the set of keys to be used for this encrypt/decrypt
    """
    keys = []
    if args.keyfile is None:
        # attempt to locate a key
        keys = find_sesame_keys()

        if len(keys) == 0:
            # ask the user to generate one
            key = ask_create_key()
            if key is not None:
                keys = [key]

        elif len(keys) >= 1:
            if args.mode == MODE_ENCRYPT or (args.mode == MODE_DECRYPT and args.try_all is False):
                # ask the user if they want to use the first key found
                if confirm("No key supplied and {0} found. Use '{1}'?".format(
                    len(keys), keys.keys()[0]
                ), default=True):
                    keys = [keys.items()[0][1]]
                else:
                    # ask the user to generate one
                    key = ask_create_key()
                    if key is not None:
                        keys = [key]
                    else:
                        return
            else:
                # --try-all flag was supplied
                keys = keys.values()
        else:
            # use the only key found
            keys = [keys.items()[0][1]]
    else:
        # create a key
        if os.path.exists(args.keyfile) is False:
            key = ask_create_key()
            if key is not None:
                keys = [key]
        else:
            # load the single key supplied
            key = read_key(os.path.join(args.keyfile))
            if key is not None:
                keys = [key]

    return keys


def find_sesame_keys():
    # use OrderedDict to maintain order in which keys are found
    keys = collections.OrderedDict()
    for root, dirs, files in os.walk(os.getcwd()):
        for filename in fnmatch.filter(files, '*.key'):
            try:
                # attempt to read the sesame key; non-keyczar files will error
                key = read_key(os.path.join(root, filename))

                # generate a relative path to the key from current working dir
                relative_path = root[len(os.getcwd()):]
                if relative_path.startswith(os.path.sep):
                    relative_path = relative_path[1:]

                keys[os.path.join(relative_path, filename)] = key

            except (ValueError, KeyError):
                pass
    return keys


def verify_input_files(inputfiles):
    # during encrypt, inputfiles is a list
    if isinstance(inputfiles, list) is False:
        inputfiles = [inputfiles]

    for f in inputfiles:
        # fail if input file doesn't exist
        if not os.path.exists(f):
            raise SesameError('File doesn\'t exist at {0}'.format(f))

        # check input not zero-length
        statinfo = os.stat(f)
        if statinfo.st_size == 0:
            raise SesameError('Input file is zero-length ({0})'.format(f))

    return True


def read_key(key_path):
    # attempt decode key with various codecs
    for codec in ('utf-8', 'latin1', 'utf-8-sig'):
        try:
            with codecs.open(key_path, 'rU', encoding=codec) as f:
                key = f.read()
                json.loads(key)
                break

        except (UnicodeDecodeError, ValueError), e:
            # retry with alternate codec
            continue
        except IOError, e:
            raise SesameError('Problem opening keyfile {0}: {1}'.format(key_path, e))

    if key is None:
        raise SesameError("Could not decode keyfile")

    # pass correctly decoded key data to keyczar
    return AesKey.Read(key)


def ask_create_key(directory=os.getcwd()):
    res = raw_input('Encryption key not provided. Create? [Y/n] ')
    if len(res) > 0 and not res.lower().startswith('y'):
        return None

    return create_key(directory)


def create_key(directory, write=True):
    # generate a new key
    key = AesKey.Generate()

    if write is True:
        # create a unique file to house our generated key
        with tempfile.NamedTemporaryFile(prefix='sesame', suffix='.key', dir=directory, delete=False) as keyfile:
            keyfile.write(str(key))

        print 'Encryption key created at {0}'.format(os.path.basename(keyfile.name))

    return key


def ask_overwrite(path, isdir=False):
    noun = 'Directory' if os.path.isdir(path) else 'File'
    return confirm(
        '{0} {1} exists. Overwrite?'.format(noun, os.path.basename(path)),
        default=False
    )


def ask_decrypt_file(filename):
    return confirm('Found {0}. Do you want to decrypt this file?'.format(filename), default=False)


def confirm(msg, default=True):
    """
    Display confirm prompt on command line

    msg:
        The message to display to the user
    default:
        Default True/False (yes/no) at the prompt
    """
    if default is True:
        display = '{0} [Y/n] '.format(msg)
    else:
        display = '{0} [y/N] '.format(msg)

    res = raw_input(display)
    if default is True:
        return True if len(res) == 0 or res.lower().startswith('y') else False
    else:
        return True if len(res) > 0 and res.lower().startswith('y') else False


@contextlib.contextmanager
def make_secure_temp_directory():
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(temp_dir)


def mkdir_p(path):
    """ http://stackoverflow.com/a/600612/425050 """
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise
