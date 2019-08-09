import rasp_runYOLOPhoto
import io
import socket
import multiprocessing
import struct # Performs conversions between Python values and C structs represented as Python strings
from PIL import Image
from datetime import datetime

# Start a socket listening for connections
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000)) # 0.0.0.0 means all interfaces
server_socket.listen(0)

# Accept a single connection and make a file-like object out of it
connection = server_socket.accept()[0].makefile('rb') # read and binary mode
processes = []
try:
    while True:
        # Read the length of the image as a 32-bit unsigned int 
        # If the length is zero, quit the loop
        image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0] # Little Endian
        if not image_len:
            break

        # Construct a stream to hold the image data and read the image data from the connection
        image_stream = io.BytesIO()
        image_stream.write(connection.read(image_len))

        # Rewind the stream, open it as an image with PIL and do processing on it
        image_stream.seek(0)
        output = datetime.now().strftime("%b_%d_%Y_%H_%M_%S_%f")
        image = Image.open(image_stream)
        image.save(output + '.jpg')
        image.verify()
        print('Image %s is verified and saved' % output)

        def yolo(name):
            rasp_runYOLOPhoto.runYOLO(name + '.jpg')
        
        process = multiprocessing.Process(target=yolo, args=(output,))
        process.start()
        processes.append(process)
    
    for t in processes:
        t.join()


finally:
    connection.close()
    server_socket.close()


# Reference: https://picamera.readthedocs.io/en/release-1.9/recipes1.html#capturing-to-a-network-stream