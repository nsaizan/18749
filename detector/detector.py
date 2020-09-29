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
lfd_messenger = Messenger(None, MY_NAME, MY_SERVER, lfd_logger)

#Macro to get a timestamp in ms.
get_time = lambda: int(round(time.time() * 1000))

hb_sent_num = 0;

# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #

# Continuously wait to receive receipts on a specified connection.
# If no receipt is received before the timeout, throw an error and exit.
def get_receipts(frequency, hb_conn):

    timeout = 1000 * NORMALIZED_TIMEOUT / frequency
    last_receipt_time = get_time()
    
    while True:

        try:
            if get_time() - last_receipt_time > timeout:
                lfd_logger.error("AHHHH! THE SERVER IS DEAD!")
                hb_conn.close()
                return

            # Wait for the server to send back receipt
            x = lfd_messenger.recv(hb_conn,25)

            #If we receive a heartbeat back from the server.
            if(x):
                last_receipt_time = get_time()

        except Exception as e:
            lfd_logger.warning("Error while getting receipt! (Connection may have closed.)")
            return
 
# Tries to connect to the heartbeat socket until it succeeds, then
# sends heartbeat messages indefinitely at the specified frequency.
def send_heartbeat(frequency, hb_conn):

    global hb_sent_num
    
    try:
        while True:
            hb_sent_num = hb_sent_num+1
            lfd_messenger.send(f"Heartbeat {hb_sent_num}")
            time.sleep(1/frequency)

    except Exception as e:
        lfd_logger.warning("Error while sending heartbeat! (Connection may have closed.)")
        return

 
 
# # # # #
# MAIN  #
# # # # #
# Parse heartbeat frequency from the input
if len(sys.argv) < 2:
    raise ValueError("No Heartbeat Frequency Provided!")
 
if len(sys.argv) > 2:
    raise ValueError("Too Many CLI Arguments!")
 
freq = int(sys.argv[1])

while True:


    hb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server on the HB socket.
    while(hb_socket.connect_ex((HOST, LFD_HB_PORT))):
        lfd_logger.warning("HB port not available.")
        time.sleep(1)

    lfd_logger.info('HB connection established')
    lfd_messenger.socket = hb_socket
    
    #Set up function to continuously send heartbeats.
    heartbeat = threading.Thread(target=send_heartbeat, args = (freq,hb_socket))
    heartbeat.start()

    receipts = threading.Thread(target=get_receipts, args=(freq,hb_socket))
    receipts.start()

    #Wait for  the two perpetual threads to die before starting the process
    #over again.
    receipts.join()
    heartbeat.join()

    hb_socket.close()


