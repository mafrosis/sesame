Sesame: config file encryption
==============================

Almost all applications have configuration of some kind, and often this config 
is sensitive - database passwords, SMTP account details, API keys etc.

These days it's common to use public source control; which means you can no
longer store your application's sensitive config with your code.

Sesame provides a simple way to encrypt (and decrypt) your application's config
so it can be safely stored in public source control.


Cryptography
------------

Sesame leans on a little known project called `keyczar <http://www.keyczar.org/>`_,
which was originally built by members of the Google Security Team.

Keyczar in turn builds upon `pycrypto <https://pypi.python.org/pypi/pycrypto>`_,
and aims to provide sane defaults for your crypto.


Installation
------------

To install sesame, simply:

.. code-block:: bash

    $ pip install sesame


Usage
-----

The interface to Sesame intentionally resembles that of ``tar``. There are only two
sub-commands: ``encrypt`` and ``decrypt`` as described below:

.. code-block:: bash

    usage: sesame encrypt [-h] [-k KEYFILE] [-f]
                          outputfile inputfile [inputfile ...]

    positional arguments:
      outputfile            Encrypted file to be created
      inputfile             Files to be encrypted

    optional arguments:
      -h, --help            show this help message and exit
      -k KEYFILE, --keyfile KEYFILE
                            Path to keyczar encryption key
      -f, --force           Force overwrite of existing encrypted file

.. code-block:: bash

    usage: sesame decrypt [-h] [-k KEYFILE] [-f] [-O OUTPUT_DIR] [-T] inputfile

    positional arguments:
      inputfile             File to be decrypted

    optional arguments:
      -h, --help            show this help message and exit
      -k KEYFILE, --keyfile KEYFILE
                            Path to keyczar encryption key
      -f, --force           Force overwrite of existing decrypted file
      -O OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Extract files into a specific directory
      -T, --try-all         Search for keys from current directory and try all of
                            them
