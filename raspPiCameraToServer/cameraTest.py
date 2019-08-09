
import picamera
import time

camera = picamera.PiCamera()
camera.capture('test.jpg')

camera.start_recording('testVid.h264')
time.sleep(5)
camera.stop_recording()

camera.start_preview()
time.sleep(10)
camera.stop_preview()
