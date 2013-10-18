import collections
import contextlib
import fnmatch
import os
import shutil
import tempfile

from keyczar.keys import AesKey


def _find_sesame_keys():
    # use OrderedDict to maintain order in which keys are found
    keys = collections.OrderedDict()
    for root, dirs, files in os.walk(os.getcwd()):
        for filename in fnmatch.filter(files, '*.key'):
            try:
                keys[filename] = _read_key(os.path.join(root, filename))
            except (ValueError, KeyError):
                pass
    return keys


def _read_key(key_path):
    with open(key_path, 'r') as f:
        data = f.read()
    return AesKey.Read(data)


def _ask_create_key():
    res = raw_input('Encryption key not provided. Create? [Y/n] ')
    if len(res) > 0 and not res.lower().startswith('y'):
        return None

    # create a unique file to house our generated key
    with tempfile.NamedTemporaryFile(prefix='sesame', suffix='.key', dir=os.getcwd(), delete=False) as keyfile:
        key = AesKey.Generate()
        keyfile.write(str(key))

    print 'Encryption key created at {0}'.format(os.path.basename(keyfile.name))
    return key


def _ask_overwrite(path, isdir=False):
    noun = 'Directory' if os.path.isdir(path) else 'File'
    return _confirm(
        '{0} {1} exists. Overwrite?'.format(noun, os.path.basename(path)),
        default=False
    )


def _ask_decrypt_file(filename):
    return _confirm('Found {0}. Do you want to decrypt this file?'.format(filename), default=False)


def _confirm(msg, default=True):
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


def _compare_files_and_dirs(a, b):
    isdira = os.path.isdir(a)
    isdirb = os.path.isdir(b)
    if isdira and not isdirb:
        return -1
    elif not isdira and isdirb:
        return 1
    else:
        return 0


@contextlib.contextmanager
def make_secure_temp_directory():
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(temp_dir)

