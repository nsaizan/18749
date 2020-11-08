#
#    File: Global Fault Detector
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

MAX_MSG_LEN = 1024 #Max number of bytes we're willing to receive at once.

member_count = 0
membership   = []
lfd_conns = []
members_lock = threading.Lock()


gfd_logger = Logger()

def add_member(server):
    global member_count
    global membership
    global members_lock

    members_lock.acquire()

    if server in membership:
        gfd_logger.warning(f"Server {server} is already a member")
    else:
        membership.append(server)
        membership.sort()
        member_count += 1
        membership_string = ", ".join(membership)
        gfd_logger.info(f"GFD: {member_count} members: {membership_string}")

    members_lock.release()

def delete_member(server):
    global member_count
    global membership
    global members_lock

    members_lock.acquire()

    if server in membership:
        membership.remove(server)
        member_count -= 1
        membership_string = ", ".join(membership)
        gfd_logger.info(f"GFD: {member_count} members: {membership_string}")
    else:
        gfd_logger.warning(f"Server {server} is not a member")

    members_lock.release()

# Continuously wait to receive receipts on a specified connection.
# If no receipt is received before the timeout, throw an error and exit.
def get_receipts(frequency, hb_conn, messenger, rm_messenger):

    hb_messenger = messenger
    
    timeout = 1000 * NORMALIZED_TIMEOUT / frequency
    last_receipt_time = get_time()
    
    while True:

        try:
            if get_time() - last_receipt_time > timeout:
                gfd_logger.error("AHHHH! THE SERVER IS DEAD!")
                hb_conn.close()
                return

            # Wait for the LFD to send back receipt
            x = hb_messenger.recv(hb_conn)

            if(x):
                # Check if this is a heartbeat.
                if("Heartbeat" in x):
                    last_receipt_time = get_time()
                # Check if this is an add membership request
                elif("add" in x):
                    args = x.split(" ")
                    requestor = args[0][0:4]
                    server_to_add = args[3]
                    add_member(server_to_add)
                    #Pass along to the RM
                    rm_messenger.send(x)
                # Check if this is a delete membership request
                elif("delete" in x):
                    args = x.split(" ")
                    requestor = args[0][0:4]
                    server_to_delete = args[3]
                    delete_member(server_to_delete)
                    #Pass along to the RM
                    rm_messenger.send(x)

        except Exception as e:
            gfd_logger.warning("Error while getting receipt! (Connection may have closed.)")
            traceback.print_exc()
            return

def heartbeat_one_lfd(frequency, hb_conn, messenger):
    #Local hb number for each thread.
    hb_sent_num = 0
    hb_messenger = messenger
    
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
    #Once in the beginning we connect to the RM. The RM is a single point of
    #failure, so we don't anticipate ever having to re-connect to it.
    rm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while(rm_socket.connect_ex((HOST, ports["RM_LISTEN"]))):
        gfd_logger.warning("RM not available.")
        time.sleep(1)

    gfd_logger.info('Registered with the RM.')
    rm_messenger = Messenger(rm_socket, "GFD", "RM", gfd_logger)

    # Identify ourself to the RM
    rm_messenger.send("GFD")
    
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

                hb_messenger = Messenger(conn, "GFD", "", gfd_logger)
                hb_messenger.recv(conn)

                #Kick off two threads: one to send heartbeats to this
                #particular LFD, and the other to get receipts back.
                heartbeat = threading.Thread(target=heartbeat_one_lfd, args = (freq, conn, hb_messenger))
                heartbeat.start()
                
                receipts = threading.Thread(target=get_receipts, args=(freq, conn, hb_messenger, rm_messenger))
                receipts.start()

                
                members_lock.acquire()
                lfd_conns.append(conn)
                members_lock.release()
                
        except Exception as e: 
            traceback.print_exc()
            s.close() #Gracefully exit by closing s & all connections.
            for conn in clients:
                conn.close()
            return

if __name__ == '__main__':

    # Parse heartbeat frequency from the input
    if len(sys.argv) < 2:
        raise ValueError("No Heartbeat Frequency Provided!")
    
    if len(sys.argv) > 2:
        raise ValueError("Too Many CLI Arguments!")
    
    freq = float(sys.argv[1])

    main(freq)
