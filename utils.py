import os

def rm(path, no_error=True):
    if os.path.exists(path):
        os.remove(path)
    elif not no_error:
        raise FileNotFoundError(f"File {path} not found")