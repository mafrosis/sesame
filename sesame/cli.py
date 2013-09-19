import argparse
import collections
import fnmatch
import os
import sys
import zlib


from keyczar.keys import AesKey
from keyczar.errors import KeyczarError

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
    subparsers = parser.add_subparsers(dest='command')

    # setup the arguments for both encrypt and decrypt
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '-c', '--config', required=True,
        help='Path to your app config')
    parent_parser.add_argument(
        '-k', '--keyfile',
        help='Path to keyczar encryption key')

    # setup parser for encrypt command
    pencrypt = subparsers.add_parser('encrypt',
        parents=[parent_parser],
        help='Encrypt a config file',
    )
    pencrypt.set_defaults(mode=MODE_ENCRYPT)
    pencrypt.add_argument(
        '-f', '--force', action='store_true',
        help='Force overwrite of existing encrypted file')

    # setup parser for decrypt command
    pdecrypt = subparsers.add_parser('decrypt',
        parents=[parent_parser],
        help='Decrypt a config file',
    )
    pdecrypt.set_defaults(mode=MODE_DECRYPT)
    pdecrypt.add_argument(
        '-f', '--force', action='store_true',
        help='Force overwrite of existing decrypted file')

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
            if args.mode == MODE_ENCRYPT:
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
        # check destination exists
        if args.force is False and os.path.exists('{0}.sesame'.format(args.config)):
            if _ask_overwrite('{0}.sesame'.format(args.config)) is False:
                return

        if not os.path.exists(args.config):
            raise ConfigError('Application config doesn\'t exist at {0}'.format(args.config))

        # encrypt the input file
        try:
            with open(args.config, 'rb') as i:
                data = keys[0].Encrypt(zlib.compress(i.read()))
        except KeyczarError as e:
            raise ConfigError(
                'An error occurred in keyczar.Encrypt\n  {0}:{1}'.format(e.__class__.__name__, e)
            )

        # write the encrypted file
        with open('{0}.sesame'.format(args.config), 'wb') as o:
            o.write(data)

        print 'Application config encrypted at {0}.sesame'.format(args.config)


    elif args.mode == MODE_DECRYPT:
        # if input file doesn't exist, and .sesame does, ask to decrypt .sesame
        if not os.path.exists(args.config) and os.path.exists('{0}.sesame'.format(args.config)):
            if _confirm('Decrypt {0}.sesame?'.format(args.config), default=True):
                output_path = args.config
                args.config = '{0}.sesame'.format(args.config)

        # fail if input file doesn't exist
        elif not os.path.exists(args.config):
            raise ConfigError('Application config doesn\'t exist at {0}'.format(args.config))

        # check input not zero-length
        statinfo = os.stat(args.config)
        if statinfo.st_size == 0:
            raise ConfigError('Input file is zero-length')

        # assume file to be decrypted ends with .sesame
        elif args.config.endswith('.sesame'):
            output_path = args.config[0:-7]

        else:
            output_path = '{0}.decrypted'.format(args.config)

        # verify existence of output_file
        if os.path.exists(output_path) and _ask_overwrite(output_path) is False:
            return

        # decrypt the input file
        for key in keys:
            try:
                with open(args.config, 'rb') as i:
                    data = zlib.decompress(key.Decrypt(i.read()))
            except KeyczarError as e:
                raise ConfigError(
                    'An error occurred in keyczar.Decrypt\n  {0}:{1}'.format(e.__class__.__name__, e)
                )

        # write the output file
        with open(output_path, 'wb') as o:
            o.write(data)

        print 'Application config decrypted at {0}'.format(output_path)


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

    key = AesKey.Generate()
    with open('sesame.key', 'w') as f:
        f.write(str(key))

    print 'Encryption key created at sesame.key'
    return key


def _ask_overwrite(filename):
    return _confirm('File {0} exists. Overwrite?'.format(filename), default=False)


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


class ConfigError(Exception):
    pass
