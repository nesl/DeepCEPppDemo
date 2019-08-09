import io
import socket
import time
import picamera

"""
Sends video stream over the network for CAPTURE_TIME seconds 
"""


# Change these
SERVER = 'Prince-Laptop'  # Hostname of server
CAM_RES_W = 1280          # Width of camera resolution
CAM_RES_H = 720           # Height of camera resolution
FRAMERATE = 30            # PiCamera's Framerate
CAPTURE_TIME = 10         # Number of seconds to record



# Connect a client socket to the server
client_socket = socket.socket()
print("Attempting to connect to " + SERVER + " ...")
client_socket.connect((SERVER, 8000))
print("Connected!")

# Make a file-like object out of the connection
connection = client_socket.makefile('wb') # write and binary mode
try:
    with picamera.PiCamera() as camera:
        camera.resolution = (CAM_RES_W, CAM_RES_H)
        camera.framerate = FRAMERATE
        
        # Start a preview and let the camera warm up for 2 seconds
        camera.start_preview()
        time.sleep(2)

        # Start recording, sending the output to the connection for CAPTURE_TIME seconds 
        print("Sending file...")
        camera.start_recording(connection, format='h264')
        camera.wait_recording(CAPTURE_TIME)
        camera.stop_recording() 

finally:
    print("Done!")
    connection.close()
    client_socket.close()


# Reference: https://picamera.readthedocs.io/en/release-1.9/recipes1.html#recording-to-a-network-stream