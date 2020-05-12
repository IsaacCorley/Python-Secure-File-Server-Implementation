import os
import copy
import socket
import argparse
from typing import Dict

import fileserve


def main(args):

    client = fileserve.Client(user=args.user, ip=args.ip, port=args.port)

    # Get user input
    while True:

        command = (
            input(
                "\nPlease enter the task you would like to perform.\n"
                + "Options are (upload_file, download_file, delete_file, "
                + "share_file, add_user):\n"
            )
            .strip()
            .lower()
        )
        print("\n")

        if command == "quit":
            print("Shutting down client.")
            break

        elif command not in [
            "upload_file",
            "download_file",
            "delete_file",
            "share_file",
            "add_user",
        ]:
            continue

        # Get additional user input based on command
        filename = ""
        if command in ["upload_file", "download_file", "delete_file", "share_file"]:
            filename = input("Enter filename: ")

        user2 = ""
        if command == "share_file":
            user2 = input("Enter user to share file with: ")

        # Run with options
        client.run(command, filename, user2)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--user", type=str, required=True, help="User interfacing with client software"
    )
    parser.add_argument("--ip", type=str, default="localhost", help="Address to use")
    parser.add_argument("--port", type=int, default=60000, help="Port to use")
    args = parser.parse_args()
    main(args)
