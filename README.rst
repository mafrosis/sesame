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

The interface to Sesame is intended to be as simple as possible. There are only two
commands: ``encrypt`` and ``decrypt`` and each of these has only two parameters
available: ``config`` and ``keyfile``.

When calling ``encrypt`` the keyfile parameter is optional - if you do not supply it,
Sesame will prompt you to generate a new key.

.. code-block:: bash

    $ sesame -h
    usage: sesame encrypt [-h] -c CONFIG [-k KEYFILE]

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            Path to your app config
      -k KEYFILE, --keyfile KEYFILE
                            Path to keyczar encryption key


Flask Bindings
--------------

When using `Flask-Script <http://flask-script.readthedocs.org/en/latest/>`_ you
can benefit from (almost) automatic integration:

.. code-block:: python

    # create your Flask app and Flask-Script manager as usual
    app = Flask("test")
    manager = Manager(app)

    # include the sesame manager
    from sesame.flask.script import manager as sesame_manager
    manager.add_command("sesame", sesame_manager)

Then sesame's encrypt/decrypt commands are available via your manage script:

.. code-block::

    $ ./manage.py sesame
    Please provide a command:
    Encrypt/decrypt Flask application config
        decrypt  Decrypt a config file
        encrypt  Encrypt a config file


Django Bindings
---------------

Coming Soon
