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
import time

# # # # # # # # # # # # #
# LFD HOST & PORT SETTINGS  #
# # # # # # # # # # # # #
HOST = '' # Local Fault Detector should be on the same machine as server
PORT = 36337
LFD_R_PORT = 36338 # Port for LFD to receive receipt


# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #
# Function to serve a single server.
def serve_LFD(conn, addr):
    while True:
        # Wait for the server to send back receipt
        x = conn.recv(25)
        if(x != b''):
            print(str(x))


def send_heartbeat(frequency):
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as heartbeat_socket:
            # Connect to the detector
            try:
                heartbeat_socket.connect((HOST, PORT))
                Flag_e = 1

                # Now just send heartbeat to server, should send through each
                # replicated server later on

                msg = "HB sent from LFD"
                heartbeat_msg = msg.encode()

                while True:
                    heartbeat_socket.send(heartbeat_msg)
                    print(msg)
                    time.sleep(int(frequency))
            except Exception as e:
                if Flag_e:
                    print("Time out, server crashed")
                    Flag_e = 0
                heartbeat_socket.close()


def receive_receipt():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Bind to the network port specified at top.
        s.bind((HOST, LFD_R_PORT))

        # This should be a listening port.
        s.listen()

        while True:
            # Wait (blocking) for connections.
            conn, addr = s.accept()

            # Start a new thread to service the client.
            server = threading.Thread(target=serve_LFD, args=(conn, addr))

            server.start()


# # # # #
# MAIN  #
# # # # #
# Parse heartbeat frequency from the input
if len(sys.argv) < 2:
    raise ValueError("No Heartbeat Frequency Provided!")

if len(sys.argv) > 2:
    raise ValueError("Too Many CLI Arguments!")

freq = sys.argv[1]


heartbeat = threading.Thread(target=send_heartbeat, args = (freq,))
heartbeat.start()
receipt = threading.Thread(target=receive_receipt, args = ())
receipt.start()