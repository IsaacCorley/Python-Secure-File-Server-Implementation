import pytest
import os
import threading

import fileserve

server = None
t = None

IP = "localhost"
PORT = 50000
USER1 = "foo1"
USER2 = "foo2"
FILENAME1 = "tmp1.txt"
FILENAME2 = "tmp2.txt"
DATA = "some plaintext message".encode()

#def test_start_server():
server = fileserve.FileServer(
    database=fileserve.Database(),
    server_address=(IP, PORT),
    handler_class=fileserve.RequestHandler
)

t = threading.Thread(target=server.serve_forever)
t.setDaemon(True)
t.start()

def test_add_user():
    response1 = server.database.add_user(user=USER1)
    response2 = server.database.add_user(user=USER2)
    print(response1)
    print(response2)
    assert USER1 in server.database.users
    assert USER2 in server.database.users

def test_upload_file():
    response1 = server.database.upload_file(
        user=USER1,
        filename=FILENAME1,
        data=DATA    
    )
    response2 = server.database.upload_file(
        user=USER2,
        filename=FILENAME2,
        data=DATA    
    )
    print(response1)
    print(response2)
    assert os.path.exists(os.path.join(server.database.FILE_DIR, FILENAME1))
    assert os.path.exists(os.path.join(server.database.FILE_DIR, FILENAME2))
    assert FILENAME1 in server.database.files
    assert FILENAME2 in server.database.files
    assert USER1 == server.database.files[FILENAME1]["owner"]
    assert USER2 == server.database.files[FILENAME2]["owner"]

def test_download_file():
    response = server.database.download_file(
        user=USER1,
        filename=FILENAME1,
    )
    print(response)
    assert isinstance(response["data"]["data"], bytes)
    assert response["data"]["data"] == DATA

def test_share_file():
    response = server.database.share_file(
        user=USER2,
        filename=FILENAME1
    )
    print(response)
    assert USER2 in server.database.files[FILENAME1]["access"]

def test_delete_file():
    response = server.database.delete_file(
        user=USER1,
        filename=FILENAME1
    )
    print(response)
    assert not os.path.exists(os.path.join(server.database.FILE_DIR, FILENAME1))

def test_shutdown_server():
    filename = "./tests/db.json"
    server.shutdown(filename)
    server.socket.close()

    assert os.path.exists(filename)