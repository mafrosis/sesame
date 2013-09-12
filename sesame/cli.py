import argparse
import sys

from sesame.core import encrypt_config, decrypt_config, ConfigError


def entrypoint():
    parser = argparse.ArgumentParser(
        description='Sesame config file encryption and decryption'
    )
    subparsers = parser.add_subparsers(dest='command')

    # setup the arguments for both encrypt and decrypt
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '-c', '--config', action='store', required=True,
        help='Path to your app config')
    parent_parser.add_argument(
        '-k', '--keyfile', action='store',
        help='Path to keyczar encryption key')

    # setup parser for encrypt command
    pencrypt = subparsers.add_parser('encrypt',
        parents=[parent_parser],
        help='Encrypt a config file',
    )
    pencrypt.set_defaults(func=encrypt_config, term='encrypt')

    # setup parser for decrypt command
    pdecrypt = subparsers.add_parser('decrypt',
        parents=[parent_parser],
        help='Decrypt a config file',
    )
    pdecrypt.set_defaults(func=decrypt_config, term='decrypt')
    pdecrypt.add_argument(
        '-f', '--force', action='store_true',
        help='Force overwrite of existing config file')

    args = parser.parse_args()

    try:
        # encrypt
        if args.term == 'encrypt':
            key_created = encrypt_config(args.config, args.keyfile)
            print 'Application config encrypted at {0}.encrypted'.format(args.config)

            if key_created is True:
                print 'Encryption key created at sesame.key'

        # decrypt
        else:
            if decrypt_config(args.config, args.keyfile, args.force):
                print 'Application config decrypted at {0}'.format(args.config)

    except ConfigError as e:
        sys.stderr.write('{0}\n'.format(e))
        sys.exit(1)
