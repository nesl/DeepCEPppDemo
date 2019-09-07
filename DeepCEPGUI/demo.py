from tkinter import *   
from tkinter import ttk 
from tkinter.messagebox import showinfo
import datetime
from enum import Enum
import pickle
import zmq
import queue
import threading

proxy_IP = '127.0.0.1'
proxy_URL = "tcp://" + proxy_IP + ":2222"


map_button_windows = dict()
rectangles = dict()
uncertainty_threashold = 0.5

# Events enumeration
class Event(Enum):
	GUNSHOT = 1
	REDTRUCK1 = 2
	REDTRUCK2 = 3
	CONVOY = 4
	COORDINATED_ATTACK = 5
	FIGHT = 6
def process_queue():
	global root
	if(root.resetGUI == True):
		print("Got reset!")
		for event in Event:
			if event in rectangles:
				canvas.delete(rectangles[event])
			if event in map_button_windows:
				canvas.delete(map_button_windows[event])
		root.resetGUI = False
	else:
		try:
			message = root.q.get(0)
			topic = message[0].decode('utf-8')
			data = pickle.loads(message[1])
			print('Received: ', topic, data)
			print('Event_type \t Sensor_ID \t Event_time\t Uncertainty')
			print('%s \t\t %s \t\t %2f \t\t %.2f \n' %(data[0], data[1], data[2], data[3]))
				
			if(topic == "CE_CONVOY" and float(data[3]) > uncertainty_threashold):
				buttons[Event.CONVOY].configure( command= lambda: popup_showinfo(topic,data[0],data[3],data[1],data[2]))
				map_button_windows[Event.CONVOY] = canvas.create_window(635, 440, anchor='nw', window=buttons[Event.CONVOY])
				rectangles[Event.CONVOY] = canvas.create_rectangle(360,300,910,430, outline='orange', width=outline_width)
			elif(topic == "CAM1" and data[0] == "red_truck" and float(data[3]) > uncertainty_threashold):
				buttons[Event.REDTRUCK1].configure( command= lambda: popup_showinfo(topic,data[0],data[3],data[1],data[2]))
				map_button_windows[Event.REDTRUCK1] = canvas.create_window(370, 340, anchor='nw', window=buttons[Event.REDTRUCK1])
				rectangles[Event.REDTRUCK1] = canvas.create_rectangle(405,380,445,420, outline='red', width=outline_width)
			elif(topic == "CAM2" and data[0] == "red_truck" and float(data[3]) > uncertainty_threashold):
				buttons[Event.REDTRUCK2].configure( command= lambda: popup_showinfo(topic,data[0],data[3],data[1],data[2]))
				map_button_windows[Event.REDTRUCK2] = canvas.create_window(815, 310, anchor='nw', window=buttons[Event.REDTRUCK2])
				rectangles[Event.REDTRUCK2] = canvas.create_rectangle(840,350,880,390, outline='red', width=outline_width)
			elif(topic == "AUDIO" and data[0] == "gunshot" and float(data[3]) > uncertainty_threashold):
				buttons[Event.GUNSHOT].configure( command= lambda: popup_showinfo(topic,data[0],data[3],data[1],data[2]))	
				map_button_windows[Event.GUNSHOT] = canvas.create_window(965, 400, anchor='nw', window=buttons[Event.GUNSHOT])
				rectangles[Event.GUNSHOT] = canvas.create_rectangle(1000,440,1040,480, outline='red', width=outline_width)
			elif(topic == "MARC_EC" and data[0] == "fight" and float(data[3]) > uncertainty_threashold):
				buttons[Event.FIGHT].configure( command= lambda: popup_showinfo(topic,data[0],data[3],data[1],data[2]))
				map_button_windows[Event.FIGHT] = canvas.create_window(965,300, anchor='nw', window = buttons[Event.FIGHT])
				rectangles[Event.FIGHT] = canvas.create_rectangle(1000,340, 1040, 380, outline='red', width=outline_width)
			elif(topic == "CE_CA" and  float(data[3]) > uncertainty_threashold):
				buttons[Event.COORDINATED_ATTACK].configure( command= lambda: popup_showinfo(topic,data[0],data[3],data[1],data[2]))
				map_button_windows[Event.COORDINATED_ATTACK] = canvas.create_window(700, 250, anchor='nw', window=buttons[Event.COORDINATED_ATTACK])
				rectangles[Event.COORDINATED_ATTACK] = canvas.create_rectangle(350,290,1070,490, outline='blue', width=outline_width)		
		except queue.Empty:
			print("Queue empty...")
	root.after(update_interval, process_queue)

class ThreadedTask(threading.Thread):
	def __init__(self, queue):
		threading.Thread.__init__(self)
		self.q = queue
	def run(self):
		while True:
			try: 
				print("Thread waiting for message...")
				message= subscriber.recv_multipart()
				print("Got message and adding to queue")
				self.q.put(message)
			except KeyboardInterrupt:
				print("Stopping...")
				
        
# Show information of an event
def popup_showinfo(title, label,confidence, sensorID,timestamp):
	global map_button_window4,canvas
	showinfo(str(title), "Label: "+str(label)+"\nConfidence: "+ str(confidence)+"\nSensor-ID: "+str(sensorID)+"\nTimestamp: "+str(timestamp)) 
	#map_button_window4 = canvas.create_window(700, 250, anchor='nw', window=map_button4)

def reset():
	global map_button_windows, canvas, root
	root.resetGUI = True
	print("Resetting...")
	
	
def toggle():
	global map_button_window4,canvas
	
	canvas.delete(map_button_window4)
	

	
# Width of rectangle outlines:
outline_width = 5

# Update time for UI in ms
update_interval = 500

# This will subscribe to all topics
topics = [b'AUDIO', b'CE_CONVOY', b'MARC_EC', b'CAM1', b'CAM2', b'CE_CA']

# Create a 0MQ Context
context = zmq.Context()

# Create a subscriber socket
subscriber = context.socket(zmq.SUB)

# Connect using environment variable
print('Connecting to: %s' % proxy_URL)

subscriber.connect(proxy_URL)

# Subscribe to each topic in the topics list
for topic in topics:
	# Python 3 treats strings and byte arrays differently
	# We are using ZMQ calls which expect byte arrays, not
	# strings so we need to convert
	if type(topic) is str:
		topic = topic.encode('utf-8')

	# Perform the subscribe
	subscriber.setsockopt(zmq.SUBSCRIBE, topic)

	# Print a message telling the user we have subscribed...
	# don't forget to convert back to a str
	print('Subscribed to topic "%s"' % (topic.decode('utf-8')))
    

# Setup Tkinter root
root = Tk()  
root.resetGUI= False
		
	
def startSub():
	# Start task thread to check if an event has occurred
	Process(target=checkEvent).start()	
	
canvas = Canvas(root, width = 1500, height = 1000)      
canvas.pack()      

# Styles for buttons:
style = ttk.Style(root)
style.configure('orange.TButton', background='orange')
style.configure('blue.TButton', background='blue')
style.configure('red.TButton', background='red')


# Buttons to add to window
buttons = dict()
buttons[Event.CONVOY] = ttk.Button(root, text = "Convoy To Town", width = 15, style='orange.TButton')
buttons[Event.GUNSHOT] = ttk.Button(root, text = "  Gun Shot", width = 10, style='red.TButton')
buttons[Event.REDTRUCK1] = ttk.Button(root, text = " Convoy",  width = 10, style='red.TButton')
buttons[Event.REDTRUCK2] = ttk.Button(root, text = " Convoy",  width = 10, style='red.TButton')
buttons[Event.COORDINATED_ATTACK] = ttk.Button(root, text = "Coord. Attack",  width = 12, style='blue.TButton')
buttons[Event.FIGHT] = ttk.Button(root, text = "  Fight",  width = 10, style='red.TButton')

img = PhotoImage(file="map.gif")      
canvas.create_image(50,50, anchor=NW, image=img)      



#map_button3 = ttk.Button(root, text = "  Gun Shot", command= lambda: popup_showinfo("Gun Shot","gunshot","0.99",1,datetime.datetime.now()),width = 10) 


reset_button = ttk.Button(root, text = "Reset", command= reset, 
                    width = 10)
reset_button.configure(style='red.TButton')   
reset_button_window = canvas.create_window(1, 1, anchor='nw', window=reset_button)

root.q = queue.Queue()
ThreadedTask(root.q).start()
root.after(update_interval, process_queue)

root.mainloop()

# Close the subscriber socket
subscriber.close()


# Terminate the context
context.term()
