#
#    File: Replication Manager
#  Author: aquinn, nsaizan, ranz2
#   Group: TheEnemy'sGateIsDown
#    Date: 11/8/2020
#
# Main code for our replication manager.

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
import threading
from ports  import ACTIVE_REPLICATION


MAX_MSG_LEN = 1024 #Max number of bytes we're willing to receive at once.

member_count = 0
membership   = []
gfd_conn = []
members_lock = threading.Lock()


rm_logger = Logger()

def send2servers(servers_list, msg):
    logger = Logger()
    for s_num in servers_list:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, ports[f"{s_num}_LISTEN"]))
        new_messenger = Messenger(s, f'RM', f"{s_num}", logger)
        new_messenger.send(msg)
        logger.info(f"{s_num}, " + msg)
        s.close()

def add_member(server):
    global member_count
    global membership
    global members_lock

    members_lock.acquire()

    if server in membership:
        rm_logger.warning(f"Server {server} is already a member")
    else:
        membership.append(server)
        # membership.sort()
        member_count += 1
        membership_string = ", ".join(membership)
        rm_logger.info(f"RM: {member_count} members: {membership_string}")

        # # # # # # # # # # # BEGIN OF RM TO SEVER # # # # # # # # # # #
        # RM should tell server what to do when membership changed
        msg2server = ""
        if ACTIVE_REPLICATION:
            if member_count == 1:
                msg2server = "You Must Set I Am Ready To True"
                server_list = [membership[0]]
            else:
                # the new joined replica should not send check point
                msg2server = "You Must Send Checkpoint"
                server_list = membership[:-1]
        else:
            if member_count == 1:
                msg2server = "You Are The Primary"
                server_list = [membership[0]]

        if msg2server != "":
            t = threading.Thread(target=send2servers,
                                  args=(server_list, msg2server),
                                  daemon=True)
            t.start()
        # # # # # # # # # # #  END OF RM TO SEVER  # # # # # # # # # # #

    members_lock.release()

def delete_member(server):
    global member_count
    global membership
    global members_lock

    members_lock.acquire()

    if server in membership:
        # # # # # # # # # # # BEGIN OF RM TO SEVER # # # # # # # # # # #
        # RM should tell server what to do when membership changed
        msg2server = ""
        if not ACTIVE_REPLICATION:
            # if delete the earliest joined replica in passive mode
            # it delete the primary, then need to choose another primary
            if server == membership[0] and member_count > 1:
                msg2server = "You Are The Primary"
                server_list = [membership[1]]

        if msg2server != "":
            t = threading.Thread(target=send2servers,
                                 args=(server_list, msg2server),
                                 daemon=True)
            t.start()
        # # # # # # # # # # #  END OF RM TO SEVER  # # # # # # # # # # #

        membership.remove(server)
        member_count -= 1
        membership_string = ", ".join(membership)
        rm_logger.info(f"RM: {member_count} members: {membership_string}")
    else:
        rm_logger.warning(f"Server {server} is not a member")

    members_lock.release()




def main():
    # Open the top-level listening socket.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        #Set the socket address so it can be reused without a timeout.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to the RM_LISTEN port.
        s.bind((HOST, ports["RM_LISTEN"]))

        # This should be a listening port.
        s.listen()

        rm_logger.info("RM Initialized! member_count="+str(member_count)) 
        
        
        #Run forever
        try:
            
            # Wait (blocking) for a single connection from the GFD.
            gfd_conn, addr = s.accept()

            rm_messenger = Messenger(gfd_conn, "RM", "GFD", rm_logger)


            while True:
                # Wait for status updates from the GFD.
                x = rm_messenger.recv(gfd_conn)

                if(x):
                    # Check if this is an add membership request
                    if("add" in x):
                        args = x.split(" ")
                        requestor = args[0][0:4]
                        server_to_add = args[3]
                        add_member(server_to_add)
                    # Check if this is a delete membership request
                    elif("delete" in x):
                        args = x.split(" ")
                        requestor = args[0][0:4]
                        server_to_delete = args[3]
                        delete_member(server_to_delete)
                    elif("GFD" in x):
                        rm_logger.info("GFD registered, 0 members")
                        
            
                
        except Exception as e: 
            traceback.print_exc()
            s.close() #Gracefully exit by closing s & all connections.
            return

if __name__ == '__main__':

    main()
