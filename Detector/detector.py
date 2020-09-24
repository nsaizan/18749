#
#    File: Server Application
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 9/14/2020
#
# Main code for our detector.

import socket
import threading
import sys

# # # # # # # # # # # # #
# LFD HOST & PORT SETTINGS  #
# # # # # # # # # # # # #
LFD_HOST = '127.0.0.1' # Local Fault Detector should be on this machine.
LFD_PORT = 36338


# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #
# Function to serve a single server.
def serve_server(conn, addr):
    while True:
        # Wait for the server to send heartbeat msg.
        x = conn.recv(5)
        if x:
            server_port = int(x)
            print('Server from port: ' + str(server_port) + ' is still alive.')
        else:
            break


# # # # #
# MAIN  #
# # # # #
# Open the top-level listening socket.
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Bind to the network port specified at top.
    s.bind((LFD_HOST, LFD_PORT))

    # This should be a listening port.
    s.listen()

    # Flavor Text
    print("\n'This is the fault detector interface.")
    print(" Should continuing receive heartbeat signal from server.")
    # Run forever
    while True:
        # Wait (blocking) for connections.
        conn, addr = s.accept()

        # Start a new thread to service the server.
        server = threading.Thread(target=serve_server, args=(conn, addr))
        server.start()
