import argparse
import collections
import contextlib
import fnmatch
import os
import shutil
import sys
import tarfile
import tempfile
import zlib

from keyczar.keys import AesKey
from keyczar.errors import KeyczarError
from keyczar.errors import InvalidSignatureError

MODE_ENCRYPT = 1
MODE_DECRYPT = 2


def entrypoint():
    try:
        args = parse_command_line()
        _main(args)
    except ConfigError as e:
        sys.stderr.write('{0}\n'.format(e))
        sys.exit(1)


def parse_command_line():
    parser = argparse.ArgumentParser(
        description='Sesame config file encryption and decryption'
    )
    subparsers = parser.add_subparsers()

    # setup the arguments for both encrypt and decrypt
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '-k', '--keyfile',
        help='Path to keyczar encryption key')

    # setup parser for encrypt command
    pencrypt = subparsers.add_parser('encrypt',
        parents=[parent_parser],
        help='Encrypt one or more files',
    )
    pencrypt.set_defaults(mode=MODE_ENCRYPT)
    pencrypt.add_argument(
        'outputfile',
        help='Encrypted file to be created')
    pencrypt.add_argument(
        'inputfile', nargs='+',
        help='Files to be encrypted')
    pencrypt.add_argument(
        '-f', '--force', action='store_true',
        help='Force overwrite of existing encrypted file')

    # setup parser for decrypt command
    pdecrypt = subparsers.add_parser('decrypt',
        parents=[parent_parser],
        help='Decrypt a file created with Sesame',
    )
    pdecrypt.set_defaults(mode=MODE_DECRYPT)
    pdecrypt.add_argument(
        'inputfile',
        help='File to be decrypted')
    pdecrypt.add_argument(
        '-f', '--force', action='store_true',
        help='Force overwrite of existing decrypted file')
    pdecrypt.add_argument(
        '-O', '--output-dir', default=os.getcwd(),
        help='Extract files into a specific directory')
    pdecrypt.add_argument(
        '-T', '--try-all', action='store_true',
        help='Search for keys from current directory and try all of them')

    return parser.parse_args()


def _main(args):
    keys = []
    if args.keyfile is None:
        # attempt to locate a key
        keys = _find_sesame_keys()

        if len(keys) == 0:
            # ask the user to generate one
            key = _ask_create_key()
            if key is not None:
                keys = [key]

        elif len(keys) > 1:
            if args.mode == MODE_ENCRYPT or (args.mode == MODE_DECRYPT and args.try_all is False):
                # ask the user if they want to use the first key found
                if _confirm('No key supplied and {0} found. Use {1}?'.format(
                    len(keys), keys.keys()[0]
                ), default=True):
                    keys = [keys.items()[0][1]]
                else:
                    # ask the user to generate one
                    key = _ask_create_key()
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
            key = _ask_create_key()
            if key is not None:
                keys = [key]
        else:
            # load the single key supplied
            key = _read_key(os.path.join(args.keyfile))
            if key is not None:
                keys = [key]

    # check user has provided a key
    if len(keys) == 0:
        raise ConfigError('No keys provided')


    if args.mode == MODE_ENCRYPT:
        # check if destination exists
        if args.force is False and os.path.exists(args.outputfile):
            if _ask_overwrite(args.outputfile) is False:
                return

        # args.inputfile is a list of files
        for f in args.inputfile:
            if not os.path.exists(f):
                raise ConfigError('File doesn\'t exist at {0}'.format(f))

        with make_secure_temp_directory() as working_dir:
            # create a tarfile of inputfiles
            with tarfile.open(os.path.join(working_dir, 'sesame.tar'), 'w') as tar:
                for name in args.inputfile:
                    tar.add(name)

            try:
                # encrypt the tarfile
                with open(os.path.join(working_dir, 'sesame.tar'), 'rb') as i:
                    with open(args.outputfile, 'wb') as o:
                        o.write(keys[0].Encrypt(zlib.compress(i.read())))
            except KeyczarError as e:
                raise ConfigError(
                    'An error occurred in keyczar.Encrypt\n  {0}:{1}'.format(e.__class__.__name__, e)
                )


    elif args.mode == MODE_DECRYPT:
        # fail if input file doesn't exist
        if not os.path.exists(args.inputfile):
            raise ConfigError('File doesn\'t exist at {0}'.format(args.inputfile))

        # check input not zero-length
        statinfo = os.stat(args.inputfile)
        if statinfo.st_size == 0:
            raise ConfigError('Input file is zero-length')

        with make_secure_temp_directory() as working_dir:
            # create a temporary file
            working_file = tempfile.mkstemp(dir=working_dir)

            success = False

            # iterate all keys; first successful key will break
            for key in keys:
                try:
                    # decrypt the input file
                    with open(args.inputfile, 'rb') as i:
                        data = zlib.decompress(key.Decrypt(i.read()))

                    # write into our working file
                    with os.fdopen(working_file[0], 'wb') as o:
                        o.write(data)

                    success = True
                    break
                except InvalidSignatureError as e:
                    if args.try_all is False:
                        raise ConfigError('Incorrect key')
                except KeyczarError as e:
                    raise ConfigError(
                        'An error occurred in keyczar.Decrypt\n  {0}:{1}'.format(
                            e.__class__.__name__, e
                        )
                    )
            # check failure
            if success is False:
                raise ConfigError('No valid keys for decryption')

            # untar the decrypted temp file
            with tarfile.open(working_file[1], 'r') as tar:
                tar.extractall(path=working_dir)


            # get the list of items in working dir and sort by directories first
            working_items = sorted(os.listdir(working_dir), cmp=_compare_files_and_dirs)

            # move all files to the current working path
            for name in working_items:
                if name != os.path.basename(working_file[1]):
                    # create some full paths
                    path = os.path.join(working_dir, name)
                    dest = os.path.join(args.output_dir, name)

                    # ask user about overwrite
                    if args.force is False and os.path.exists(dest):
                        if _ask_overwrite(dest) is True:
                            if os.path.isdir(dest):
                                shutil.rmtree(dest)
                            else:
                                os.remove(dest)
                        else:
                            continue

                    # move file to cwd
                    shutil.move(path, dest)


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


class ConfigError(Exception):
    pass
