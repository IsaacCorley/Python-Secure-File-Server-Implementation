import os
import pickle
from typing import Dict


def read_file(file_dir: str, filename: str) -> bytes:
    """ Read file contents to bytes """
    with open(os.path.join(file_dir, filename), "rb") as f:
        data = f.read()
    return data

def save_file(file_dir: str, filename: str, data: bytes):
    """ Save to file to 'database' """
    with open(os.path.join(file_dir, filename), "wb") as f:
        f.write(data)

def serialize(data: Dict) -> bytes:
    """ Pickle dictionary object to bytes for sending """
    return pickle.dumps(data)

def deserialize(data: bytes) -> Dict:
    """ Unpickle the received dictionary object """
    return pickle.loads(data)
