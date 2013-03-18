import sys

from flask.ext.script import Manager

from sesame.core import encrypt_config, decrypt_config, ConfigError

manager = Manager(usage="Encrypt/decrypt Flask application config")


@manager.option("-c", "--config",
                help="Path to your Flask app config")
@manager.option("-k", "--keyfile",
                help="Path to keyczar encryption key")
def encrypt(config, keyfile=None):
    "Encrypt a config file"
    try:
        config = encrypt_config(config, keyfile)
        if config is not None:
            print "Application config encrypted at {0}".format(config)

    except ConfigError as e:
        sys.stderr.write("{0}\n".format(e))
        sys.exit(1)


@manager.option("-c", "--config",
                help="Path to your encrypted app config")
@manager.option("-k", "--keyfile",
                help="Path to keyczar encryption key")
def decrypt(config, keyfile):
    "Decrypt a config file"
    try:
        config = decrypt_config(config, keyfile)
        if config:
            print "Application config decrypted at {0}".format(config)

    except ConfigError as e:
        sys.stderr.write("{0}\n".format(e))
        sys.exit(1)
