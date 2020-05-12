import copy
from typing import Tuple, Dict

from fileserve.server import response_template


SUCCESS = 0
FAILURE = 1


def error_check_request(request: Dict, users: Dict, files: Dict) -> Tuple[int, Dict]:
    """ Check for errors in request before processing """

    response = copy.deepcopy(response_template)

    if request["header"] == "upload_file":
        # User1 doesn't exist
        if request["data"]["user1"] not in users:
            response["data"]["error"] = "user1 {} doesn't exist".format(
                request["data"]["user1"]
            )

        # Filename wrong format
        elif request["data"]["filename"] == "":
            response["data"]["error"] = "filename {} is empty str".format(
                request["data"]["filename"]
            )

        # File already exists
        elif request["data"]["filename"] in files:
            response["data"]["error"] = "filename {} already exists".format(
                request["data"]["filename"]
            )

        # Data is empty
        elif request["data"]["data"] == "" or request["data"]["data"] == b"":
            response["data"]["error"] = "data {} is empty".format(
                request["data"]["data"]
            )

    elif request["header"] == "download_file":
        # User1 doesn't exist
        if request["data"]["user1"] not in users:
            response["data"]["error"] = "user1 {} doesn't exist".format(
                request["data"]["user1"]
            )

        # Filename wrong format
        elif request["data"]["filename"] == "":
            response["data"]["error"] = "filename {} is empty str".format(
                request["data"]["filename"]
            )

        # File doesn't exist
        elif request["data"]["filename"] not in files:
            response["data"]["error"] = "filename {} doesn't exist".format(
                request["data"]["filename"]
            )

        # User1 doesn't have access to share file
        elif request["data"]["user1"] not in files[request["data"]["filename"]]["access"]:
            response["data"][
                "error"
            ] = "user1 {} not authorized to download file {}".format(
                request["data"]["user1"], request["data"]["filename"]
            )

    elif request["header"] == "delete_file":
        # User1 doesn't exist
        if request["data"]["user1"] not in users:
            response["data"]["error"] = "user1 {} doesn't exist".format(
                request["data"]["user1"]
            )

        # Filename wrong format
        elif request["data"]["filename"] == "":
            response["data"]["error"] = "filename {} is empty str".format(
                request["data"]["filename"]
            )

        # File doesn't exist
        elif request["data"]["filename"] not in files:
            response["data"]["error"] = "filename {} doesn't exist".format(
                request["data"]["filename"]
            )

        # User1 doesn't have access to delete file
        elif request["data"]["user1"] != files[request["data"]["filename"]]["owner"]:
            response["data"][
                "error"
            ] = "user1 {} not authorized to delete file {}".format(
                request["data"]["user1"], request["data"]["filename"]
            )

    elif request["header"] == "share_file":
        # User1 doesn't exist
        if request["data"]["user1"] not in users:
            response["data"]["error"] = "user1 {} doesn't exist".format(
                request["data"]["user1"]
            )

        # User2 doesn't exist
        elif request["data"]["user2"] not in users:
            response["data"]["error"] = "user2 {} doesn't exist".format(
                request["data"]["user2"]
            )

        # Filename wrong format
        elif request["data"]["filename"] == "":
            response["data"]["error"] = "filename {} is empty str".format(
                request["data"]["filename"]
            )

        # File doesn't exist
        elif request["data"]["filename"] not in files:
            response["data"]["error"] = "filename {} doesn't exist".format(
                request["data"]["filename"]
            )

        # User1 doesn't have access to share file
        elif request["data"]["user1"] != files[request["data"]["filename"]]["owner"]:
            response["data"][
                "error"
            ] = "user1 {} not authorized to share file {}".format(
                request["data"]["user1"], request["data"]["filename"]
            )

        # User2 already has access to file
        elif request["data"]["user2"] in files[request["data"]["filename"]]["access"]:
            response["data"]["error"] = "user2 {} already has read access to file {}".format(
                request["data"]["user2"], request["data"]["filename"]
            )

    elif request["header"] == "add_user":
        # User already exists so can't add
        if request["data"]["user1"] in users:
            response["data"]["error"] = "user1 {} already exists".format(
                request["data"]["user1"]
            )

    else:
        response["data"]["error"] = "unknown header"

    if response["data"]["error"] == "":
        return SUCCESS, response
    else:
        return FAILURE, response
