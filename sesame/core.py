import os
import shutil
import tarfile
import tempfile
import zlib

from keyczar.errors import KeyczarError
from keyczar.errors import InvalidSignatureError

from sesame.utils import ask_overwrite
from sesame.utils import make_secure_temp_directory
from sesame.utils import mkdir_p


def encrypt(inputfiles, outputfile, keys):
    with make_secure_temp_directory() as working_dir:
        # create a tarfile of inputfiles
        with tarfile.open(os.path.join(working_dir, 'sesame.tar'), 'w') as tar:
            for name in inputfiles:
                # TODO use warning to prompt user here
                if os.path.isabs(name):
                    # fix absolute paths, same as tar does
                    tar.add(name, arcname=name[1:])
                elif name.startswith('..'):
                    # skip relative paths
                    pass
                else:
                    tar.add(name)

        try:
            # encrypt the tarfile
            with open(os.path.join(working_dir, 'sesame.tar'), 'rb') as i:
                with open(outputfile, 'wb') as o:
                    o.write(keys[0].Encrypt(zlib.compress(i.read())))
        except KeyczarError as e:
            raise SesameError(
                'An error occurred in keyczar.Encrypt\n  {0}:{1}'.format(e.__class__.__name__, e)
            )


def decrypt(inputfile, keys, force=False, output_dir=None, try_all=False):
    with make_secure_temp_directory() as working_dir:
        # create a temporary file
        working_file = tempfile.mkstemp(dir=working_dir)

        success = False

        # iterate all keys; first successful key will break
        for key in keys:
            try:
                # decrypt the input file
                with open(inputfile, 'rb') as i:
                    data = zlib.decompress(key.Decrypt(i.read()))

                # write into our working file
                with os.fdopen(working_file[0], 'wb') as o:
                    o.write(data)

                success = True
                break
            except InvalidSignatureError as e:
                if try_all is False:
                    raise SesameError('Incorrect key')
            except KeyczarError as e:
                raise SesameError(
                    'An error occurred in keyczar.Decrypt\n  {0}:{1}'.format(
                        e.__class__.__name__, e
                    )
                )

        # check failure
        if success is False:
            raise SesameError('No valid keys for decryption')

        if tarfile.is_tarfile(working_file[1]):
            # untar the decrypted temp file
            with tarfile.open(working_file[1], 'r') as tar:
                tar.extractall(path=working_dir)

            # get list of full paths to all files in working dir
            # ignoring the decrypted tarfile
            working_items = [
                os.path.join(rootdir[len(working_dir)+1:], filename)
                for rootdir, dirnames, filenames in os.walk(working_dir)
                for filename in filenames if filename != os.path.basename(working_file[1])
            ]

            for filename in working_items:
                # move all files to the output path
                move_output_file(
                    path=os.path.join(working_dir, filename),
                    dest=os.path.join(output_dir, filename),
                    force=force,
                )

        else:
            # older versions of Sesame didn't wrap a tarfile and
            # encrypted only a single file at a time
            working_items = [os.path.join(working_dir[len(working_dir)+1:], )]

            # attempt to create an output filename using old Sesame logic
            if inputfile.endswith(".encrypted"):
                move_output_file(
                    path=working_file[1],
                    dest=os.path.join(output_dir, inputfile[0:-10]),
                    force=force,
                )
            else:
                # create a secure random-named file
                with tempfile.NamedTemporaryFile(suffix='.sesame-decrypted', dir=output_dir, delete=False) as keyfile:
                    keyfile.write("\0")

                # overwrite the file just created with the decrypted file
                move_output_file(
                    path=working_file[1],
                    dest=os.path.join(output_dir, keyfile.name),
                    force=True,
                )


def move_output_file(path, dest, force=False):
    # ask user about overwrite
    if force is False and os.path.exists(dest):
        if ask_overwrite(dest) is False:
            return

    # ensure destination dirs exist
    mkdir_p(os.path.dirname(dest))

    # move file to output_dir
    shutil.copy(path, dest)


class SesameError(Exception):
    pass
