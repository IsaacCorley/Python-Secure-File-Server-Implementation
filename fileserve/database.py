import os
import copy
import json
import pickle
from typing import Tuple, Dict

from fileserve import utils
from fileserve import crypto
from fileserve.server import response_template
from fileserve.error_handling import error_check_request


files_template = {
    "owner": "",
    "access": []
}

user_template = {
    "info": ""
}

class Database(object):

    def __init__(self):
        self.DB_DIR = "db"
        self.FILE_DIR = os.path.join(self.DB_DIR, "files")
        self.KEY_DIR = "pki"
        self.db_file = "db.json"
        self.user = "server"

        self.files, self.users = self.load()
        self.pub_key, self.priv_key = self.load_keys()
        print("Files: \n", self.files)
        print("Users: \n", self.users)

    def load(self) -> Tuple[Dict, Dict]:
        """ Load the database from file """
        os.makedirs(self.FILE_DIR, exist_ok=True)
        os.makedirs(self.KEY_DIR, exist_ok=True)
        os.makedirs(self.DB_DIR, exist_ok=True)

        if os.path.exists(os.path.join(self.DB_DIR, self.db_file)):
            with open(os.path.join(self.DB_DIR, self.db_file), "r") as f:
                db = json.load(f)

            return db["files"], db["users"]

        else:
            return {}, {}

    def save(self, filename=None):
        """ Save database to file """
        if filename is None:
            filename = os.path.join(self.DB_DIR, self.db_file)

        with open(filename, "w") as f:
            json.dump({"files": self.files, "users": self.users}, f, indent=1)

    def load_keys(self) -> Tuple[str, str]:
        """ Load pub/priv keys """

        pub_key_path = os.path.join(self.KEY_DIR, "{}_public.pem".format(self.user))
        priv_key_path = os.path.join(self.DB_DIR, "{}_private.pem".format(self.user))

        if not os.path.exists(pub_key_path) or not os.path.exists(priv_key_path):
            print("Server does not have public/private keys so generating them...")
            self.generate_keys()

        # Load public and private keys
        """ Load keys from pem files """
        with open(pub_key_path, "r") as f:
            pub_key = f.read()

        with open(priv_key_path, "r") as f:
            priv_key = f.read()

        return pub_key, priv_key

    def generate_keys(self):
        """ Generate keys for a user """
        pub_key, priv_key = crypto.generate_keys()
        
        with open(os.path.join(self.KEY_DIR, self.user + "_public.pem"), "wb") as f:
            f.write(pub_key)

        with open(os.path.join(self.DB_DIR, self.user + "_private.pem"), "wb") as f:
            f.write(priv_key)

    def load_user_key(self, user: str) -> str:
        """ Load the public key of a given user from the PKI """
        path = os.path.join(self.KEY_DIR, "{}_public.pem".format(user))
        with open(path, "r") as f:
            pub_key = f.read()

        return pub_key

    def error_check(self, request: Dict) -> Tuple[int, Dict]:
        """ Perform error checking on the request """
        return error_check_request(request, self.users, self.files)

    def add_user(self, user: str, data=None) -> Dict:
        """ Add a user to the database """

        # Update access control matrix
        self.users[user] = user_template.copy()

        # Format response
        response = copy.deepcopy(response_template)
        response["header"] = "success"
        return response

    def upload_file(self, user: str, filename: str, data: bytes) -> Dict:
        """ Upload a file to the server and update the access control matrix """
        # Save file to server
        utils.save_file(self.FILE_DIR, filename, data)

        # Update access control matrix
        self.files[filename] = files_template.copy()
        self.files[filename]["owner"] = user
        self.files[filename]["access"].append(user)

        # Format response
        response = copy.deepcopy(response_template)
        response["header"] = "success"
        return response

    def download_file(self, user: str, filename: str) -> Dict:
        """ Send a file to the client """
        # Read file
        data = utils.read_file(self.FILE_DIR, filename)

        # Format response
        response = copy.deepcopy(response_template)
        response["header"] = "success"
        response["data"]["filename"] = filename
        response["data"]["data"] = data
        return response

    def delete_file(self, user: str, filename: str) -> Dict:
        """ Delete file specified by the client """
        # Delete file from server
        os.remove(os.path.join(self.FILE_DIR, filename))

        # Update access control matrix
        del self.files[filename]

        # Format response
        response = copy.deepcopy(response_template)
        response["header"] = "success"
        return response

    def share_file(self, user: str, filename: str) -> Dict:
        """ Give access in the access control matrix to user2 for a file """
        # Update access control matrix
        self.files[filename]["access"].append(user)

        # Format response
        response = copy.deepcopy(response_template)
        response["header"] = "success"
        return response

    def encrypt_response(self, user: str, response: Dict) -> Dict:
        """ Encrypt the request data excluding the header """
        # Serialize the data dict
        data = utils.serialize(response["data"])

        # Load user's public key
        pub_key = self.load_user_key(user)
        
        # Encrypt and sign + MAC for integrity
        ciphertext, mac = crypto.rsa_encrypt(data, pub_key, self.priv_key)
        response["data"] = ciphertext
        response["mac"] = mac
        
        return response

    def decrypt_request(self, request: Dict) -> Dict:
        """ Decrypt the request data excluding the header """

        # Load user's public key
        pub_key = self.load_user_key(request["sender"])

        # Decrypt the data dict and verify MAC and signature
        plaintext = crypto.rsa_decrypt(
            ciphertext=request["data"],
            mac=request["mac"],
            pub_key=pub_key,
            priv_key=self.priv_key
        )
        
        # Deserialize data dict
        request["data"] = utils.deserialize(plaintext)

        return request