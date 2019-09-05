
import time
import zmq
import pickle
from pprint import pprint


PUB_IP = "192.168.8.224"
PUB_URL = "tcp://" + PUB_IP + ":1111"


# Sends topic and body to publisher
def print_and_pub(publisher, topic, body):

    if type(topic) is str:
        btopic = topic.encode('utf-8')
    else:
        btopic = topic
        topic = topic.decode('utf-8')


    if type(body) is str:
        bbody = body.encode('utf-8')
    elif type(body) is list:
        bbody = pickle.dumps(body)
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

            time.sleep(0.5)

            num += 1
            
            counter -= 1

        print_and_pub(publisher, 'system', 'Finished publishing messages')
    
    
    
def setup():
    # Create a ZMQ Context
    context = zmq.Context()
	
	# Create a publisher socket
    publisher = context.socket(zmq.PUB)
    
    # Connect
    print ("Connecting to: %s" % PUB_URL)
    publisher.connect(PUB_URL)
    
    return publisher
    
    
def main():

    publisher = setup()

    # SEND
    try:
        sendDefault(publisher)

    except KeyboardInterrupt:
        print("Stopping...")

    finally:

        # Close the publisher socket
        publisher.close()

        # Terminate the context
        context.term()
        
	
	
if __name__ == "__main__":
    main()
