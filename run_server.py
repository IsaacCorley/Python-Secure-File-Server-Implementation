import os
import argparse
import threading

import fileserve


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="localhost", help="Address to use")
    parser.add_argument("--port", type=int, default=60000, help="Port to use")
    args = parser.parse_args()

    server = fileserve.FileServer(
        database=fileserve.Database(),
        server_address=(args.ip, args.port),
        handler_class=fileserve.RequestHandler
    )
    ip, port = server.server_address

    t = threading.Thread(target=server.serve_forever)
    t.setDaemon(True)
    t.start()
    
    print("Server running on IP: {}, Port: {}".format(ip, port))

    # Wait for user input to shutdown server
    signal = ""
    while signal != "kill":
        signal = input("Enter 'kill' to shutdown server: ").lower()

    server.shutdown()
    server.socket.close()
