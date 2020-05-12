# FileServe: A Secure DropBox Clone

Pure Python implementation of a secure Dropbox/Google Drive clone, that provides client/server file interface using RSA public-key cryptography.

Note this implementation was written in Python 3.7.

### Install Requirements

```bash
pip3 install -r requirements.txt

```

### Run File Server

```bash
python3 run_server.py --ip localhost --port 60000


Output:

Server running on IP: 127.0.0.1, Port: 60000
Enter 'kill' to shutdown server:

```

### Run Client

```bash
python3 run_client.py --user alice --ip localhost --port 60000

Please enter the task you would like to perform.
Options are (upload_file, download_file, delete_file, share_file, add_user):

add_user: registers a user to the file server

upload_file: uploads a file from local to server

download_file: downloads a file from server to local

delete_file: deletes a file from the server

share_file: shares read access to a file to another user

```

### Run Tests

```bash
pytest -ra

```
