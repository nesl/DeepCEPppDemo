"""
Records DURATION seconds from the sound card and plays the recording
"""


import os
import subprocess
from time import sleep

DURATION = 2

count = 0
while True:
		
	# Record
	print(str(count) + ": Record")
	"""
	-D = Device, -d = Duration, -f = File Directory/name, -c = Channels
	"""
	try:
		subprocess.call(['arecord', '-D', 'hw:1,0', '-d', '{}'.format(DURATION), '-f', 'cd', 'test.wav', '-c', '1'])
	except KeyboardInterrupt:
		exit(0)

	
	
	# Play
	print(str(count) + ": Play")
	try:
		subprocess.call(['aplay', 'test.wav'])
		print("\n")
	except KeyboardInterrupt:
		exit(0)

	
	count += 1
