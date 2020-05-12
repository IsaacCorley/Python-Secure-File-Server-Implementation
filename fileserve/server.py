import os
import time
import pickle
import socketserver
from typing import Dict

from fileserve import utils


SUCCESS = 0
FAILURE = 1

request_template = {
    "header": "",
    "sender": "",
    "mac": "",
    "data": {
        "filename": "",
        "user1": "",
        "user2": "",
        "data": ""
    },
}

response_template = {
    "header": "failure",
    "mac": "",
    "data": {
        "filename": "",
        "data": "",
        "error": ""
    },
}


class RequestHandler(socketserver.StreamRequestHandler):

    def handle(self):
        """ Receive data, process, and return a response """
        print("\nHandling New Request")
        data = self.recvall(chunksize=64)

        # Unpickle data
        request = utils.deserialize(data)

        # Decrypt data
        if request["header"] != "add_user":
            request = self.server.database.decrypt_request(request)
            print(request)

        # Process request and generate a response
        response = self.process_request(request)

        # Encrypt data in response
        if request["header"] != "add_user":
            response = self.server.database.encrypt_response(
                request["sender"],
                response
            )
            print(response)

        # Pickle the response
        response = utils.serialize(response)

        # Send the respone
        self.send(response)

    def send(self, response: bytes):
        """ Send response data """
        self.sendlen(response)
        self.request.send(response)

    def sendlen(self, response: bytes):
        """ Send the length of the data first """
        length = str(len(response)).encode()
        self.request.send(length)
        time.sleep(0.05)

    def recvlen(self) -> int:
        """ Receive length of data to be received """
        length = self.request.recv(32)
        length = int(length.decode())
        return length

    def recvall(self, chunksize: int = 8192) -> bytes:
        """ Receive entirety of data """
        length = self.recvlen()
        data = b""
        
        while len(data) < length:
            received = self.request.recv(chunksize)

            if not received:
                break
            else:
                data += received

        return data

    def process_request(self, request: Dict) -> Dict:
        """ Main function to parse received data and call other functions """

        # Check for errors in request
        signal, response = self.server.database.error_check(request)

        if signal == FAILURE:
            print("Error check returned an issue")
            return response

        if request["header"] == "upload_file":
            response = self.server.database.upload_file(
                request["data"]["user1"],
                request["data"]["filename"],
                request["data"]["data"],
            )
            print(
                "User {} uploaded file {}".format(
                request["data"]["user1"],
                request["data"]["filename"],
            ))

        elif request["header"] == "download_file":
            response = self.server.database.download_file(
                request["data"]["user1"], request["data"]["filename"]
            )
            print(
                "User {} downloaded a file {}".format(
                request["data"]["user1"],
                request["data"]["filename"],
            ))

        elif request["header"] == "delete_file":
            response = self.server.database.delete_file(
                request["data"]["user1"], request["data"]["filename"]
            )
            print(
                "User {} deleted file {}".format(
                request["data"]["user1"],
                request["data"]["filename"],
            ))

        elif request["header"] == "share_file":
            response = self.server.database.share_file(
                request["data"]["user2"],
                request["data"]["filename"],
            )
            print(
                "User {} shared a file {} with user {}".format(
                request["data"]["user1"],
                request["data"]["filename"],
                request["data"]["user2"]
            ))

        elif request["header"] == "add_user":
            response = self.server.database.add_user(
                request["data"]["user1"], request["data"]["data"]
            )
            print("Added user {}".format(request["data"]["user1"]))

        return response


class FileServer(socketserver.ThreadingMixIn, socketserver.TCPServer):

    allow_reuse_address = True
    request_queue_size = 20
    daemon_threads = True

    def __init__(
        self,
        database,
        server_address=("localhost", 60000),
        handler_class=RequestHandler,
    ):
        self.database = database
        socketserver.TCPServer.__init__(self, server_address, handler_class)

    def shutdown(self, filename=None):
        self.database.save(filename)
        return socketserver.TCPServer.shutdown(self)
