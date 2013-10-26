import collections
import contextlib
import errno
import fnmatch
import os
import shutil
import tempfile

from keyczar.keys import AesKey


def find_sesame_keys():
    # use OrderedDict to maintain order in which keys are found
    keys = collections.OrderedDict()
    for root, dirs, files in os.walk(os.getcwd()):
        for filename in fnmatch.filter(files, '*.key'):
            try:
                keys[filename] = read_key(os.path.join(root, filename))
            except (ValueError, KeyError):
                pass
    return keys


def read_key(key_path):
    with open(key_path, 'r') as f:
        data = f.read()
    return AesKey.Read(data)


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
