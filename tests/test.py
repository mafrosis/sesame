import collections
import mock
import os
import shutil
import tempfile
import time
import uuid

from sesame.core import decrypt
from sesame.core import encrypt

from sesame.utils import create_key
from sesame.utils import make_secure_temp_directory

from utils import cd
from utils import mkdir_p
from utils import delete_path


class TestSesame(object):
    def setup(self):
        """
        Create a working directory and some test files
        """
        self.working_dir = tempfile.mkdtemp()
        self.file_contents = collections.OrderedDict.fromkeys([
            'file.test',
            '1/file.test',
            '2/2/file.test',
        ])
        self.file_timestamps = self.file_contents.copy()

        # create a key for the tests
        self.key = create_key(None, write=False)

        # setup files in subdirectory
        for path in self.file_contents.keys():
            # create file content
            self.file_contents[path] = str(uuid.uuid4())

            abspath = os.path.join(self.working_dir, path)

            # create subdirs as necessary
            mkdir_p(os.path.dirname(abspath))

            # create test file in dir
            with open(abspath, 'w') as f:
                f.write(self.file_contents[path])

            # record file creation time
            self.file_timestamps[path] = os.stat(abspath).st_ctime

    def teardown(self):
        """
        Destroy working directory
        """
        shutil.rmtree(self.working_dir)


    def testcreate_key(self):
        pass


    def test_single_relative(self):
        """
        Simple auto-gen key; relative paths; deletes source file
        """
        # use only the first test file
        test_file_path = self.file_contents.keys()[0]

        with cd(self.working_dir):
            # encrypt the test file
            encrypt(
                inputfiles=[test_file_path],
                outputfile='sesame.encrypted',
                keys=[self.key],
            )

            # delete the source file
            os.remove(test_file_path)

            # decrypt the test file
            decrypt(
                inputfile='sesame.encrypted',
                keys=[self.key],
                output_dir=os.getcwd(),         # default in argparse
            )

            # ensure file has been created
            assert os.path.exists(test_file_path)

            # verify decrypted contents
            with open(test_file_path, 'r') as f:
                assert self.file_contents[test_file_path] == f.read()


    def test_single_relative_force(self):
        """
        Simple auto-gen key; relative paths; with force flag to overwrite source file
        """
        # use only the first test file
        test_file_path = self.file_contents.keys()[0]

        with cd(self.working_dir):
            # encrypt the test file
            encrypt(
                inputfiles=[test_file_path],
                outputfile='sesame.encrypted',
                keys=[self.key],
            )

            # sleep before decrypt to ensure file ctime is different
            time.sleep(1)

            # decrypt the test file
            decrypt(
                inputfile='sesame.encrypted',
                keys=[self.key],
                output_dir=os.getcwd(),         # default in argparse
                force=True,
            )

            # ensure file has been overwritten
            assert self.file_timestamps[test_file_path] < os.stat(test_file_path).st_ctime

            # verify decrypted contents
            with open(test_file_path, 'r') as f:
                assert self.file_contents[test_file_path] == f.read()


    def test_single_relative_overwrite_true(self):
        """
        Simple auto-gen key; relative paths; answer yes to overwrite the source file
        """
        # use only the first test file
        test_file_path = self.file_contents.keys()[0]

        with cd(self.working_dir):
            # encrypt the test file
            encrypt(
                inputfiles=[test_file_path],
                outputfile='sesame.encrypted',
                keys=[self.key],
            )

            # sleep before decrypt to ensure file ctime is different
            time.sleep(1)

            # decrypt the test file; mock responds yes to overwrite the existing file
            with mock.patch('__builtin__.raw_input', return_value='y'):
                decrypt(
                    inputfile='sesame.encrypted',
                    keys=[self.key],
                    output_dir=os.getcwd(),         # default in argparse
                )

            # ensure file has been overwritten
            assert self.file_timestamps[test_file_path] < os.stat(test_file_path).st_ctime

            # verify decrypted contents
            with open(test_file_path, 'r') as f:
                assert self.file_contents[test_file_path] == f.read()


    def test_single_relative_overwrite_false(self):
        """
        Simple auto-gen key; relative paths; answer no to overwrite the source file
        """
        # use only the first test file
        test_file_path = self.file_contents.keys()[0]

        with cd(self.working_dir):
            # encrypt the test file
            encrypt(
                inputfiles=[test_file_path],
                outputfile='sesame.encrypted',
                keys=[self.key],
            )

            # sleep before decrypt to ensure file ctime is different
            time.sleep(1)

            # decrypt the test file; mock responds no to overwrite the existing file
            with mock.patch('__builtin__.raw_input', return_value='n'):
                # decrypt the test file
                decrypt(
                    inputfile='sesame.encrypted',
                    keys=[self.key],
                    output_dir=os.getcwd(),         # default in argparse
                )

            # ensure no file has been decrypted
            assert self.file_timestamps[test_file_path] == os.stat(test_file_path).st_ctime


    def test_single_relative_output_dir(self):
        """
        Simple auto-gen key; relative paths; deletes source file; change output directory
        """
        # use only the first test file
        test_file_path = self.file_contents.keys()[0]

        with cd(self.working_dir):
            # encrypt the test file
            encrypt(
                inputfiles=[test_file_path],
                outputfile='sesame.encrypted',
                keys=[self.key],
            )

            # create a new temporary directory to extract into
            with make_secure_temp_directory() as output_dir:
                # decrypt the test file
                decrypt(
                    inputfile='sesame.encrypted',
                    keys=[self.key],
                    output_dir=output_dir
                )

                # ensure file has been created in the output_dir
                assert os.path.exists(os.path.join(output_dir, test_file_path))

                # verify decrypted contents
                with open(os.path.join(output_dir, test_file_path), 'r') as f:
                    assert self.file_contents[test_file_path] == f.read()


    def test_single_absolute(self):
        """
        Simple auto-gen key; absolute paths
        """
        # use only the first test file
        test_file_path = self.file_contents.keys()[0]

        with cd(self.working_dir):
            # encrypt the test file
            encrypt(
                inputfiles=[os.path.join(self.working_dir, test_file_path)],
                outputfile=os.path.join(self.working_dir, 'sesame.encrypted'),
                keys=[self.key],
            )

            # delete the source file
            os.remove(test_file_path)

            # sleep before decrypt to ensure file ctime is different
            time.sleep(1)

            # decrypt the test file
            decrypt(
                inputfile=os.path.join(self.working_dir, 'sesame.encrypted'),
                keys=[self.key],
                output_dir=os.getcwd(),         # default in argparse
            )

            # the file will be extracted on the absolute path
            test_file_path_abs = os.path.join(self.working_dir, test_file_path)[1:]

            # verify decrypted contents at the absolute extracted path
            with open(test_file_path_abs, 'r') as f:
                assert self.file_contents[test_file_path] == f.read()


    def test_multiple_relative(self):
        """
        Test a directory hierarchy with relative paths
        """
        with cd(self.working_dir):
            # encrypt all the test files
            encrypt(
                inputfiles=self.file_contents.keys(),
                outputfile='sesame.encrypted',
                keys=[self.key],
            )

            # delete the source files
            for path in self.file_contents.keys():
                delete_path(path)

            # decrypt the test files
            decrypt(
                inputfile='sesame.encrypted',
                keys=[self.key],
                output_dir=os.getcwd(),         # default in argparse
            )

            for test_file_path in self.file_contents.keys():
                # ensure files have been created
                assert os.path.exists(test_file_path)

                # verify decrypted contents
                with open(test_file_path, 'r') as f:
                    assert self.file_contents[test_file_path] == f.read()


    def test_multiple_absolute(self):
        """
        Test a directory hierarchy with absolute paths
        """
        # convert the files list to absolute paths
        test_input_files = [
            os.path.join(self.working_dir, path) for path in self.file_contents.keys()
        ]

        with cd(self.working_dir):
            # encrypt all the test files
            encrypt(
                inputfiles=test_input_files,
                outputfile='sesame.encrypted',
                keys=[self.key],
            )

            # delete the source files
            for path in self.file_contents.keys():
                delete_path(path)

            # decrypt the test files
            decrypt(
                inputfile='sesame.encrypted',
                keys=[self.key],
                output_dir=os.getcwd(),         # default in argparse
            )

            for test_file_path in self.file_contents.keys():
                # the file will be extracted on the absolute path
                test_file_path_abs = os.path.join(self.working_dir, test_file_path)[1:]

                # verify decrypted contents at the absolute extracted path
                with open(test_file_path_abs, 'r') as f:
                    assert self.file_contents[test_file_path] == f.read()
