#
#    File: Local Fault Detector
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 9/27/2020
#
# Main code for our local fault detector.

import socket
import threading
import time
import sys
import traceback
import subprocess
sys.path.append("..")

# Custom imports
from helper import Logger
from helper import Messenger
from ports  import ports
from ports  import HOST
from ports  import AUTO_RESPAWN


#In units of the heartbeat period.
#i.e. for a value of 5, the detector will time out if 5 heartbeat periods
#pass without receiving a receipt.
NORMALIZED_TIMEOUT = 1

MAX_MSG_LEN = 1024 #Max number of bytes we're willing to receive at once.

#Determined at runtime
MY_NAME = None
MY_SERVER = None

#Logger instance for the LFD
lfd_logger = None
hb_messenger = None
gfd_messenger = None

#Macro to get a timestamp in ms.
get_time = lambda: int(round(time.time() * 1000))

hb_sent_num = 0


# # # # # # # # # # # # #
# THREAD FUNCTION DEFNS #
# # # # # # # # # # # # #

# Continuously wait to receive receipts on a specified connection.
# If no receipt is received before the timeout, throw an error and exit.
def get_receipts(frequency, hb_conn):
    #The status of this LFD's server
    server_is_initialized = False

    timeout = 1000 * NORMALIZED_TIMEOUT / frequency
    last_receipt_time = get_time()
    
    while True:

        try:
            if (get_time() - last_receipt_time) > timeout:
                lfd_logger.error("AHHHH! THE SERVER IS DEAD!")
                gfd_messenger.send(f"{MY_NAME}: delete replica {MY_SERVER}")
                hb_conn.close()
                return

            # Wait for the server to send back receipt
            x = hb_messenger.recv(hb_conn)

            #If we receive a heartbeat back from the server.
            if(x):
                last_receipt_time = get_time()
                # If this is the server's first hb then we tell the GFD
                if(server_is_initialized == False):
                    gfd_messenger.send(f"{MY_NAME}: add replica {MY_SERVER}")
                    server_is_initialized = True

        except Exception:
            lfd_logger.warning("Error while getting receipt! (Connection may have closed.)")
            gfd_messenger.send(f"{MY_NAME}: delete replica {MY_SERVER}")
            hb_conn.close()
            traceback.print_exc()
            return
 
# Tries to connect to the heartbeat socket until it succeeds, then
# sends heartbeat messages indefinitely at the specified frequency.
def send_heartbeat(frequency, hb_conn):

    global hb_sent_num
    
    try:
        while True:
            hb_sent_num = hb_sent_num+1
            hb_messenger.send(f"Heartbeat {hb_sent_num}")
            time.sleep(1/frequency)

    except Exception:
        lfd_logger.warning("Error while sending heartbeat! (Connection may have closed.)")
        return


# Function to receive heartbeats from the GFD and reply to them.
def serve_GFD(gfd_conn):
      
    try:
        while(1):
            # Wait for the GFD to send a heartbeat and echo it back.
            msg = gfd_messenger.recv(gfd_conn)
            if msg:
                gfd_messenger.send(msg)     

    except KeyboardInterrupt:
        print("Killing GFD heartbeat thread.")
        exit()

def main():
    #Once in the beginning we connect to the GFD. The GFD is a single point of
    #failure, so we don't anticipate ever having to re-connect to it.
    gfd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while(gfd_socket.connect_ex((HOST, ports["GFD_LISTEN"]))):
        lfd_logger.warning("GFD not available.")
        time.sleep(1)

    lfd_logger.info('Registered with the GFD.')
    gfd_messenger.socket = gfd_socket

    # Identify ourself to the GFD
    gfd_messenger.send(MY_NAME)

    gfd_heartbeat = threading.Thread(target=serve_GFD, args = (gfd_socket,))
    gfd_heartbeat.start()

    while True:


        hb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Avoid respawning too many replicas on startup
        initialized = False
        
        # Connect to the server on the HB socket.
        while(hb_socket.connect_ex((HOST, ports[MY_SERVER+"_HB"]))):
            lfd_logger.warning("HB port not available.")

            # Respawn server replica
            if(initialized and AUTO_RESPAWN):
                lfd_logger.warning(f"Respawning {MY_SERVER}")
                subprocess.call([f"./respawn_replica.sh", f"{replica_num}"])
            
            initialized = True
            time.sleep(3)

        lfd_logger.info('HB connection established')
        hb_messenger.socket = hb_socket
        
        #Set up function to continuously send heartbeats.
        heartbeat = threading.Thread(target=send_heartbeat, args = (freq, hb_socket))
        heartbeat.start()

        receipts = threading.Thread(target=get_receipts, args=(freq, hb_socket))
        receipts.start()

        #Wait for  the two perpetual threads to die before starting the process
        #over again.
        receipts.join()
        heartbeat.join()

        hb_socket.close()

if __name__ == '__main__':

    # Parse heartbeat frequency from the input
    if len(sys.argv) < 2:
        raise ValueError("No Replica Number Provided!")

    if len(sys.argv) < 3:
        raise ValueError("No Heartbeat Frequency Provided!")
    
    if len(sys.argv) > 3:
        raise ValueError("Too Many CLI Arguments!")

    replica_num = int(sys.argv[1])
    freq = float(sys.argv[2])

    MY_NAME = "LFD" + str(replica_num)
    MY_SERVER = "S" + str(replica_num)

    #Logger instance for the LFD
    lfd_logger = Logger()
    hb_messenger = Messenger(None, MY_NAME, MY_SERVER, lfd_logger)
    gfd_messenger = Messenger(None, MY_NAME, "GFD", lfd_logger)

    main()

