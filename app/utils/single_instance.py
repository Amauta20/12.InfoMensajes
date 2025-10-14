import os
import sys
import tempfile

def get_lock_file_path():
    return os.path.join(tempfile.gettempdir(), 'infomensajero.lock')

def get_arg_file_path():
    return os.path.join(tempfile.gettempdir(), 'infomensajero.arg')

def is_already_running():
    lock_file = get_lock_file_path()
    if os.path.exists(lock_file):
        return True
    
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        return False
    except IOError:
        return True

def cleanup_lock_file():
    lock_file = get_lock_file_path()
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except OSError:
            pass

def send_argument_to_running_instance():
    if len(sys.argv) > 1:
        arg_file = get_arg_file_path()
        with open(arg_file, 'w') as f:
            f.write(sys.argv[1])

