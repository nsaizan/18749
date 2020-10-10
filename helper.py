import time

class Logger:
    def __init__(self):
        self.info(f"Logger initialized")

    def msg(self, message):
        self.get_time()
        print(f"{self.recorded_time} | MSG   | {message}")

    def info(self, message):
        self.get_time()
        print(f"{self.recorded_time} | INFO  | {message}")

    def warning(self, message):
        self.get_time()
        print(f"{self.recorded_time} | WARN  | {message}")

    def error(self, message):
        self.get_time()
        print(f"{self.recorded_time} | ERROR | {message}")

    def get_time(self):
        self.recorded_time = time.asctime((time.gmtime()))[11:-5]
        return self.recorded_time

class Messenger:
    def __init__(self, socket, us, them, logger=None):
        self.socket = socket
        self.us = us
        self.them = them
        if logger == None:
            self.logger = Logger()
        else:
            self.logger = logger

    def send(self, message):
        # Append metadata
        source = self.us
        dest = self.them
        metadata = f"{source}::{dest}::"
        data = message
        message = f"{metadata}{message}"

        # Pad message
        message = f"{message}::"
        message = f"{message:<1024}"

        # Encode message
        message = message.encode()

        self.logger.get_time()
        self.socket.send(message)

        # Log the message
        self.log_send(data)

    def recv(self, conn):
        #try:
            # Check for incoming message
        msg = str(conn.recv(1024))[2:-1] # Need to remove the b'x' formatting
        if (msg):
            # Get message source, dest, content
            args = msg.split("::")
            self.them = args[0]
            self.us = args[1]
            data = args[2]

            # Log the message
            self.log_recv(data)

            result = data
        else:
            result = None
            
        return result

    def log_send(self, message):
        self.logger.msg(f"Source:{self.us} Dest:{self.them} | {message}")

    def log_recv(self, message):
        self.logger.msg(f"Source:{self.them} Dest:{self.us} | {message}")

    def info(self, message):
        self.logger.info(f"Source:{self.us} Dest:{self.them} | {message}")

    def error(self, message):
        self.logger.error(f"Source:{self.us} Dest:{self.them} | {message}")

    

    
