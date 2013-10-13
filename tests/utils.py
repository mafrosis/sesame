import contextlib
import errno
import os
import shutil


@contextlib.contextmanager
def cd(new_path):
    """ Context manager for changing the current working directory """
    saved_path = os.getcwd()
    try:
        os.chdir(new_path)
        yield new_path
    finally:
        os.chdir(saved_path)


def mkdir_p(path):
    """ http://stackoverflow.com/a/600612/425050 """
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


def delete_path(path):
    """
    Delete a path, be it file or directory
    """
    path = _get_path_base(path)
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def _get_path_base(path):
    """
    Reduce a path to it's base element

    etc/path/file.txt -> etc
    path/file.txt -> path
    file.txt -> file.txt
    """
    parts = os.path.split(path)
    if len(parts[0]) == 0:
        return parts[1]
    else:
        return _get_path_base(parts[0])
