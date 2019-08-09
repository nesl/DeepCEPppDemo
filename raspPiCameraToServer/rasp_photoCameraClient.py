import io
import socket
import struct
import time
import picamera

# Change these
SERVER = 'Prince-Laptop'  # Hostname of server
CAM_RES_W = 640           # Width of camera resolution
CAM_RES_H = 480           # Height of camera resolution
MODE = 'SHOTS'            # Select between 'SHOTS' or 'TIME'
SHOTS = 5                 # Number of images to capture (SHOTS mode)
CAPTURE_TIME = 3          # Number of seconds to capture images (TIME mode)
DELAY = 0.5               # Delay in seconds between captures


# Connect a client socket to the server
client_socket = socket.socket()
client_socket.connect((SERVER, 8000))

# Make a file-like object out of the connection
connection = client_socket.makefile('wb') # write and binary mode
try:
    with picamera.PiCamera() as camera:
        camera.resolution = (CAM_RES_W, CAM_RES_H)
        camera.start_preview()   # Start a preview and let the camera warm up
        time.sleep(0.5)

        # Note the start time and construct a stream to hold image data
        # temporarily (we could write it directly to connection but in this
        # case we want to find out the size of each capture first to keep protocol simple)
        start = time.time()
        stream = io.BytesIO()
        for num, foo in enumerate(camera.capture_continuous(stream, 'jpeg')):
            # Write the length of the capture to the stream and flush to ensure it gets sent
            connection.write(struct.pack('<L', stream.tell()))
            connection.flush()

            # Rewind the stream and send the image data
            stream.seek(0)
            connection.write(stream.read())

            # If we've been capturing for more than CAPTURE_TIME, quit
            if MODE == 'TIME' and time.time() - start > CAPTURE_TIME:
              break
            elif MODE == 'SHOTS' and num + 1 >= SHOTS:
                break

            # Reset the stream for the next capture
            stream.seek(0)
            stream.truncate()
            time.sleep(DELAY)

    # Write a length of zero to the stream to signal we're done
    connection.write(struct.pack('<L', 0))

finally:
    connection.close()
    client_socket.close()


# Reference: https://picamera.readthedocs.io/en/release-1.9/recipes1.html#capturing-to-a-network-stream