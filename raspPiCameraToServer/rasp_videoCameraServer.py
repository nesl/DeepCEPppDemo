import rasp_runYOLOVideo
import io
import socket
import subprocess
from datetime import datetime
"""
from PIL import Image

"""

# Start a socket listening for connections
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000)) # 0.0.0.0 means all interfaces
print("Waiting for connections..")
server_socket.listen(0)

# Accept a single connection and make a file-like object out of it
connection = server_socket.accept()[0].makefile('rb') # read and binary mode
print("Connected!")
try:
    outputName = datetime.now().strftime("%b_%d_%Y_%H_%M_%S_%f") + '.h264'

    with open(outputName, 'wb') as file:
        print("Transferring..")
        while True:
            # Repeatedly read 1k of data from the connection and write it to file
            data = connection.read(1024)
            if not data:
                break
            file.write(data)
     
    rasp_runYOLOVideo.runYOLO(outputName)
    
    
finally:
    print("Done!")
    connection.close()
    server_socket.close()


# Reference: https://picamera.readthedocs.io/en/release-1.9/recipes1.html#recording-to-a-network-stream