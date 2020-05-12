import os
import time
import copy
import socket
import pickle
from typing import Tuple, Dict

from fileserve import utils
from fileserve import crypto
from fileserve.server import request_template


class Client(object):

    def __init__(self, user, ip="localhost", port=60000):
        self.user = user
        self.ip = ip
        self.port = port
        self.KEY_DIR = "pki"
        self.FILE_DIR = user

        # Make user's file directory
        os.makedirs(self.FILE_DIR, exist_ok=True)
        os.makedirs(self.KEY_DIR, exist_ok=True)

        # Load keys or generate if none
        self.pub_key, self.priv_key, self.server_pub_key = self.load_keys()

        print("\nHello {}".format(self.user.capitalize()))

    def load_keys(self) -> Tuple[str, str, str]:
        """ Load public/priv/and server pub keys """

        pub_key_path = os.path.join(self.KEY_DIR, "{}_public.pem".format(self.user))
        priv_key_path = os.path.join(self.FILE_DIR, "{}_private.pem".format(self.user))
        server_key_path = os.path.join(self.KEY_DIR, "server_public.pem")

        if not os.path.exists(pub_key_path) or not os.path.exists(priv_key_path):
            print("User does not have public/private keys so generating them...")
            self.generate_keys()

        # Load public and private keys
        """ Load keys from pem files """
        with open(pub_key_path, "r") as f:
            pub_key = f.read()

        with open(priv_key_path, "r") as f:
            priv_key = f.read()
            
        with open(server_key_path, "r") as f:
            server_pub_key = f.read()

        return pub_key, priv_key, server_pub_key

    def generate_keys(self):
        """ Generate keys for a user """
        pub_key, priv_key = crypto.generate_keys()

        with open(os.path.join(self.KEY_DIR, self.user + "_public.pem"), "wb") as f:
            f.write(pub_key)

        with open(os.path.join(self.FILE_DIR, self.user + "_private.pem"), "wb") as f:
            f.write(priv_key)

    def run(self, command: str, filename: str, user2: str):
        """ Main function """

        # Generate request
        request = self.generate_request(command, filename, user2)

        FLAG = True
        if command == "add_user":
            FLAG = False

        # Encrypt and serialize request
        request = self.format_request(request, encrypt=FLAG)

        # Communicate with server
        response = self.communicate(request)

        # Deserialize and decrypt response
        response = self.parse_response(response, decrypt=FLAG)

        # Do a thing given the response
        self.process_response(response)

    def generate_request(self, command: str, filename: str, user2: str) -> Dict:
        """ Use user input to generate request """
        request = copy.deepcopy(request_template)
        request["header"] = command
        request["sender"] = self.user
        request["data"]["user1"] = self.user

        if command in ["upload_file", "download_file", "delete_file", "share_file"]:
            request["data"]["filename"] = filename

        if command == "share_file":
            request["data"]["user2"] = user2

        elif command == "upload_file":
            request["data"]["data"] = utils.read_file(
                self.FILE_DIR,
                request["data"]["filename"]
            )

        return request

    def communicate(self, request: bytes) -> bytes:
        """ Communicate with server and receive a response """

        # Connect to the server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.ip, self.port))

        # Send request
        self.sendlen(s, request)
        self.send(s, request)

        # Receive response
        response = self.recvall(s)
        s.close()

        return response

    def encrypt_request(self, request: Dict) -> Dict:
        """ Encrypt the request data excluding the header """
        # Serialize the data dict
        data = utils.serialize(request["data"])

        # Encrypt and sign + MAC for integrity
        ciphertext, mac = crypto.rsa_encrypt(data, self.server_pub_key, self.priv_key)
        request["data"] = ciphertext
        request["mac"] = mac

        return request

    def decrypt_response(self, response: Dict) -> Dict:
        """ Decrypt the response data excluding the header """
        # Decrypt the data dict and verify MAC and signature
        plaintext = crypto.rsa_decrypt(
            ciphertext=response["data"],
            mac=response["mac"],
            pub_key=self.server_pub_key,
            priv_key=self.priv_key
        )
        
        # Deserialize data dict
        response["data"] = utils.deserialize(plaintext)

        return response

    def format_request(self, request: Dict, encrypt: bool = True) -> bytes:
        """ Formatting and encrypt request """

        if encrypt:
            request = self.encrypt_request(request)

        request = utils.serialize(request)
        return request

    def parse_response(self, response: bytes, decrypt: bool = True) -> Dict:
        """ Parse response """

        response = utils.deserialize(response)

        if decrypt:
            response = self.decrypt_response(response)

        return response

    def process_response(self, response: Dict):
        """ Perform postprocessing given the response """
        print(response)

        if response["header"] == "success":
            print("Success!")
            # If file then download it
            if response["data"]["filename"] != "":
                utils.save_file(
                    self.FILE_DIR,
                    response["data"]["filename"],
                    response["data"]["data"]
                )
        else:
            print("Request failed due to {}".format(response["data"]["error"]))

    def send(self, s: socket.socket, request: bytes):
        """ Format request as binary and send to server """
        _ = s.sendall(request)

    def sendlen(self, s: socket.socket, request: bytes):
        """ Send length of data first """
        length = str(len(request)).encode()
        _ = s.send(length)
        time.sleep(0.1)

    def recvlen(self, s: socket.socket) -> int:
        """ Receive length of data to be received """
        length = s.recv(32)
        length = int(length.decode())
        return length

    def recvall(self, s: socket.socket, chunksize: int = 8192) -> bytes:
        """ Receive entirety of data """
        length = self.recvlen(s)

        data = b""

        while len(data) < length:
            received = s.recv(chunksize)

            if not received:
                break
            else:
                data += received

        return data
