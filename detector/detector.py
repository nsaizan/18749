#
#    File: Local Fault Detector
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 9/27/2020
#
# Main code for our detector.

import socket
import threading
import time
import sys
sys.path.append("..")

# Custom imports
from helper import Logger
from helper import Messenger
from server.server import HEARTBEAT_FREQ_DEFAULT

# # # # # # # # # # # # #
# LFD HOST & PORT SETTINGS  #
# # # # # # # # # # # # #
HOST = '127.0.0.1'
PORT = 36337
LFD_HOST = '127.0.0.1' # Local Fault Detector should be on this machine.
LFD_HB_PORT = 36338
LFD_R_PORT = 36339

#In units of the heartbeat period.
NORMALIZED_TIMEOUT = 5

logger = Logger()

get_time = lambda: int(round(time.time() * 1000))

# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #
# Function to serve a single server.
def serve_LFD(conn, addr, frequency):

    timeout = 1000 * NORMALIZED_TIMEOUT / frequency
    last_receipt_time = int(round(time.time() * 1000))
    
    while True:

        if get_time() - last_receipt_time > timeout:
            print("AHHHH! THE SERVER IS DEAD!")
            exit()
            
        # Wait for the server to send back receipt
        x = conn.recv(25)
        
        if(x != b''):
            last_receipt_time = get_time()
            print(str(x))
 
 
def send_heartbeat(frequency):
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as heartbeat_socket:
            # Connect to the server on the HB port.
            while(heartbeat_socket.connect_ex((HOST, LFD_HB_PORT))):
                  print("HB port not available.")
                  time.sleep(1)

            print('HB connection established')
                # Now just send heartbeat to server, should send through each
                # replicated server later on

            try:
                while True:
                    heartbeat_socket.send(b'h')
                    print('Heartbeat sent from LFD1 to S1')
                    time.sleep(1/frequency)
                    
            except Exception as e:
                print("Error while sending heartbeat. Quitting!")
                return
 
def receive_receipt():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Bind to the network port specified at top.
        s.bind((HOST, LFD_R_PORT))
 
        # This should be a listening port.
        s.listen()
 
        # Wait (blocking) for connections to the R port.
        conn, addr = s.accept()

        server = threading.Thread(target=serve_LFD, args=(conn, addr,freq))

        server.start()
 
 
# # # # #
# MAIN  #
# # # # #
# Parse heartbeat frequency from the input
if len(sys.argv) < 2:
    raise ValueError("No Heartbeat Frequency Provided!")
 
if len(sys.argv) > 2:
    raise ValueError("Too Many CLI Arguments!")
 
freq = int(sys.argv[1])


receipt = threading.Thread(target=receive_receipt, args = ())
receipt.start() 
heartbeat = threading.Thread(target=send_heartbeat, args = (freq,))
heartbeat.start()

