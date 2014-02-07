import argparse
import os
import sys

from sesame import __version__

from sesame.core import decrypt
from sesame.core import encrypt
from sesame.core import SesameError

from sesame.utils import ask_create_key
from sesame.utils import ask_overwrite
from sesame.utils import confirm
from sesame.utils import find_sesame_keys
from sesame.utils import read_key

MODE_ENCRYPT = 1
MODE_DECRYPT = 2


def entrypoint():
    try:
        # setup and run argparse
        args = parse_command_line()

        # ensure input is good
        if verify_input_files(args.inputfile):
            # locate encryption keys
            keys = get_keys(args)

            # check we have a key
            if len(keys) == 0:
                raise SesameError('No keys provided')

            # run encrypt/decrypt
            main(args, keys)

    except SesameError as e:
        sys.stderr.write('{0}\n'.format(e))
        sys.exit(1)


def parse_command_line():
    parser = argparse.ArgumentParser(
        description='Sesame config file encryption and decryption'
    )
    subparsers = parser.add_subparsers()

    # print the current sesame version
    parser.add_argument(
        '-v', '--version', action='version',
        version='sesame {0}'.format(__version__),
        help='Print the current Sesame version')

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


def main(args, keys):
    if args.mode == MODE_ENCRYPT:
        # check if destination exists
        if args.force is False and os.path.exists(args.outputfile):
            if ask_overwrite(args.outputfile) is False:
                return

        encrypt(
            inputfiles=args.inputfile,
            outputfile=args.outputfile,
            keys=keys
        )

    elif args.mode == MODE_DECRYPT:
        decrypt(
            inputfile=args.inputfile,
            keys=keys,
            force=args.force,
            output_dir=args.output_dir,
            try_all=args.try_all
        )
