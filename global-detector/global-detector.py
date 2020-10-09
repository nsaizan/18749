#
#    File: Local Fault Detector
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 10/9/2020
#
# Main code for our global fault detector.

import socket
import sys
import threading
import traceback
import time
sys.path.append("..")

from helper import Logger
from helper import Messenger
from ports import ports
from ports import HOST

#Macro to get a timestamp in ms.
get_time = lambda: int(round(time.time() * 1000))

#In units of the heartbeat period.
#i.e. for a value of 5, the detector will time out if 5 heartbeat periods
#pass without receiving a receipt.
NORMALIZED_TIMEOUT = 5

member_count = 0
membership   = []
lfd_conns = []
members_lock = threading.Lock()


gfd_logger = Logger()

# Continuously wait to receive receipts on a specified connection.
# If no receipt is received before the timeout, throw an error and exit.
def get_receipts(frequency, hb_conn, my_lfd):

    hb_messenger = Messenger(hb_conn, "GFD", my_lfd, gfd_logger)
    
    timeout = 1000 * NORMALIZED_TIMEOUT / frequency
    last_receipt_time = get_time()
    
    while True:

        try:
            if get_time() - last_receipt_time > timeout:
                gfd_logger.error("AHHHH! THE SERVER IS DEAD!")
                hb_conn.close()
                return

            # Wait for the server to send back receipt
            x = hb_messenger.recv(hb_conn,25)

            #If we receive a heartbeat back from the server.
            if(x):
                last_receipt_time = get_time()

        except Exception as e:
            gfd_logger.warning("Error while getting receipt! (Connection may have closed.)")
            traceback.print_exc()
            return

def heartbeat_one_lfd(frequency, hb_conn, my_lfd):
    #Local hb number for each thread.
    hb_sent_num = 0
    hb_messenger = Messenger(hb_conn, "GFD", my_lfd, gfd_logger)
    
    try:
        while True:
            hb_sent_num = hb_sent_num+1
            hb_messenger.send(f"Heartbeat {hb_sent_num}")
            time.sleep(1/frequency)

    except Exception as e:
        gfd_logger.warning("Error while sending heartbeat! (Connection may have closed.)")
        traceback.print_exc()
        return


def main(freq):
    # Open the top-level listening socket.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        #Set the socket address so it can be reused without a timeout.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to the GFD_LISTEN port.
        s.bind((HOST, ports["GFD_LISTEN"]))

        # This should be a listening port.
        s.listen()

        gfd_logger.info("GFD Initialized! member_count="+str(member_count)) 
        

        #server = threading.Thread(target=serve_clients, args=(), daemon=True)
        #server.start();
        
        #Run forever
        try:
            while True:
            
                # Wait (blocking) for connections from LFDs
                conn, addr = s.accept()

                my_lfd = "LFD??" #TODO

                #Kick off two threads: one to send heartbeats to this
                #particular LFD, and the other to get receipts back.
                heartbeat = threading.Thread(target=heartbeat_one_lfd, args = (freq,conn,my_lfd))
                heartbeat.start()
                
                receipts = threading.Thread(target=get_receipts, args=(freq,conn,my_lfd))
                receipts.start()

                
                members_lock.acquire()
                lfd_conns.append(conn)
                members_lock.release()
                
        except Exception as e: 
            traceback.print_exc()
            s.shutdown()
            s.close() #Gracefully exit by closing s & all connections.
            for conn in clients:
                conn.shutdown()
                conn.close()
            return


# # # # #
# MAIN  #
# # # # #
# Parse heartbeat frequency from the input
if len(sys.argv) < 2:
    raise ValueError("No Heartbeat Frequency Provided!")
 
if len(sys.argv) > 2:
    raise ValueError("Too Many CLI Arguments!")
 
freq = float(sys.argv[1])

main(freq)