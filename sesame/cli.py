from __future__ import absolute_import

import argparse
import os
import sys

from . import __version__
from . import SesameError
from . import MODE_ENCRYPT, MODE_DECRYPT

from .core import decrypt
from .core import encrypt

from .utils import ask_overwrite
from .utils import get_keys
from .utils import verify_input_files


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
        sys.stderr.flush()
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
