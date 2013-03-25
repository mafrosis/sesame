import argparse
import sys

from sesame.core import encrypt_config, decrypt_config, ConfigError


def entrypoint():
    parser = argparse.ArgumentParser(
        description='Sesame config file encryption and decryption'
    )
    subparsers = parser.add_subparsers(dest='command')

    # parser for the options on encrypt
    pencrypt = subparsers.add_parser('encrypt',
        help='Encrypt a config file'
    )
    pencrypt.set_defaults(func=encrypt_config, term='encrypted')

    pencrypt.add_argument(
        '-c', '--config', action='store', required=True,
        help='Path to your app config')
    pencrypt.add_argument(
        '-k', '--keyfile', action='store',
        help='Path to keyczar encryption key')

    # parser for the options on decrypt
    pdecrypt = subparsers.add_parser('decrypt',
        help='Decrypt a config file'
    )
    pdecrypt.set_defaults(func=decrypt_config, term='decrypted')

    pdecrypt.add_argument(
        '-c', '--config', action='store', required=True,
        help='Path to your encrypted app config')
    pdecrypt.add_argument(
        '-k', '--keyfile', action='store', required=True,
        help='Path to your keyczar encryption key')

    args = parser.parse_args()

    try:
        # call the relevant function
        conf_path = args.func(args.config, args.keyfile)
        if conf_path:
            print 'Application config {0} at {1}'.format(args.term, conf_path)

    except ConfigError as e:
        sys.stderr.write('{0}\n'.format(e))
        sys.exit(1)
