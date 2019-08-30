
import time
import zmq
from pprint import pprint

import random
import pickle


# PUB_IP = "192.168.8.212"
PUB_IP = "127.0.0.1"
# CAM_NAME = "AUDIO"

PUB_URL = "tcp://" + PUB_IP + ":1111"


# Sends topic and body to publisher
def print_and_pub(publisher, topic, body):
    
    topic = CAM_NAME

    if type(topic) is str:
        btopic = topic.encode('utf-8')
    else:
        btopic = topic
        topic = topic.decode('utf-8')

    if type(body) is str:
        bbody = body.encode('utf-8')
    elif type(body) is list:
        string = ""
        for i in body:
            string += str(i) + " "
        bbody = string.encode('utf-8')
    else:
        bbody = body
        body = body.decode('utf-8')

    publisher.send_multipart([btopic, bbody])
    print("[%s] %s" % (topic, body))
    
    """
    SAMPLE OUTPUT
    [CAM1] ['sofa', 1, 1566894623.9373112, 0.984]
    [CAM1] ['chair', 1, 1566894623.9388084, 0.71]
    [CAM1] ['chair', 1, 1566894623.940219, 0.604]
    """



# topic and messages for testing
def sendDefault(publisher):
    
    # Setup control vars
    counter = 0
    msg_count = 0
    num_messages = 10

    num = 0
    
    while True:
        counter = num_messages

        print_and_pub(publisher, 'system', 'Preparing to publish...')
        
        #Sleep 3 seconds
        time.sleep(3.0)

        print_and_pub(publisher, 'system', 'Publishing messages')

        while counter > 0:

            # Use modules to alternate topic 
            if num % 2 == 0:
                topic = 'data-1'
            else:
                topic = 'data-2'
                
            payload = 'Message number %s' % (num)

            print_and_pub(publisher, topic, payload)

            time.sleep(0.1)

            num += 1
            
            counter -= 1

        print_and_pub(publisher, 'system', 'Finished publishing messages')


def sendInput(publisher):
    start_time = time.time()
    while True:
        # keep sending events to server 
        while True:
            
            event_time = time.time()-start_time
            event_uncertainty = random.uniform(0.8, 1)
#             event_sid = 0
#             camera_img = get_img(event_time)
#             event_obj = object_detector(camera_img, yolo, all_classes)
            event_obj, event_sid = input("Enter EventType and sensorID: ").split() 
            event = [event_obj, event_sid, event_time, event_uncertainty]
            
            topic = event_sid
            if type(topic) is str:
                btopic = topic.encode('utf-8')
            else:
                btopic = topic
                topic = topic.decode('utf-8')
            
            data=pickle.dumps(event)
            publisher.send_multipart([btopic, data])
            print("sending: ", "[%s] "%topic, event)
            
        if data == 'exit':
            break
    
    
def setup():
    # Create a ZMQ Context
    context = zmq.Context()
	
	# Create a publisher socket
    publisher = context.socket(zmq.PUB)
    
    # Connect
    print ("Sending to proxy: %s" % PUB_URL)
    publisher.connect(PUB_URL)
    
    return publisher
    
    
def main():

    publisher = setup()

    # SEND
    try:
#         sendDefault(publisher)
        sendInput(publisher)

    except KeyboardInterrupt:
        print("Stopping...")

    finally:

        # Close the publisher socket
        publisher.close()

        # Terminate the context
        context.term()
        
	
	
if __name__ == "__main__":
    main()
