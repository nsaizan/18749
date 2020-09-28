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
HOST = '127.0.0.1'     # Host for the server (this PC)
PORT = 36337           # Main Server Port
LFD_HOST = '127.0.0.1' # Local Fault Detector should be on this machine.
LFD_HB_PORT = 36338    # Heartbeat port (LFD->S)
LFD_R_PORT = 36339     # Heartbeat receipt port (S->LFD)

#In units of the heartbeat period.
#i.e. for a value of 5, the detector will time out if 5 heartbeat periods
#pass without receiving a receipt.
NORMALIZED_TIMEOUT = 5

#Hardcoded for now, change these when we have >1 replica.
MY_NAME = 'LFD1'
MY_SERVER = 'S1'

#Logger instance for the LFD
lfd_logger = Logger()

#Macro to get a timestamp in ms.
get_time = lambda: int(round(time.time() * 1000))

hb_sent_num = 0;
hb_recv_num = 0;

# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #

# Continuously wait to receive receipts on a specified connection.
# If no receipt is received before the timeout, throw an error and exit.
def wait_for_receipts(conn, addr, frequency):

    global hb_recv_num
    
    timeout = 1000 * NORMALIZED_TIMEOUT / frequency
    last_receipt_time = get_time()
    
    while True:

        if get_time() - last_receipt_time > timeout:
            lfd_logger.error("AHHHH! THE SERVER IS DEAD!")
            exit()
            
        # Wait for the server to send back receipt
        x = conn.recv(25)

        #If we receive a heartbeat back from the server.
        if(x):
            last_receipt_time = get_time()
            hb_recv_num = hb_recv_num+1
            lfd_logger.info(f"{MY_NAME} got HB {hb_recv_num} from {MY_SERVER}")
 
# Tries to connect to the heartbeat socket until it succeeds, then
# sends heartbeat messages indefinitely at the specified frequency.
def send_heartbeat(frequency):

    global hb_sent_num
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as heartbeat_socket:
        
        # Connect to the server on the HB port.
        while(heartbeat_socket.connect_ex((HOST, LFD_HB_PORT))):
            lfd_logger.warning("HB port not available.")
            time.sleep(1)

        print('HB connection established')


        try:
            while True:
                heartbeat_socket.send(b'h')
                hb_sent_num = hb_sent_num+1
                lfd_logger.info(f"{MY_NAME} sent HB {hb_sent_num} to {MY_SERVER}")
                time.sleep(1/frequency)

        except Exception as e:
            lfd_logger.warning("Error while sending heartbeat! (Connection may have closed.)")
            return



# Sets up a listening socket on LFD_R_PORT, waits for the server to connect,
# then kicks off an instance of wait_for_receipts() and closes the listening
# port.
def setup_receipt():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Bind to the network port specified at top.
        s.bind((HOST, LFD_R_PORT))
 
        # This should be a listening port.
        s.listen()
 
        # Wait (blocking) for connections to the R port.
        conn, addr = s.accept()

        server = threading.Thread(target=wait_for_receipts, args=(conn,addr,freq))

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


receipt = threading.Thread(target=setup_receipt, args = ())
receipt.start() 
heartbeat = threading.Thread(target=send_heartbeat, args = (freq,))
heartbeat.start()

