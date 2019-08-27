import argparse
import time
import zmq
from pprint import pprint

SUB_IP = "127.0.0.1"
SUB_URL = "tcp://" + SUB_IP + ":8888"


"""
SAMPLE OUTPUT
Received: [CAM1] sofa 1 1566894623.9373112 0.984 
Received: [CAM1] chair 1 1566894623.9388084 0.71 
Received: [CAM1] chair 1 1566894623.940219 0.604
"""


def main():
    
    # Create a ZMQ Context
    context = zmq.Context()

    # Create a subscriber socket
    subscriber = context.socket(zmq.SUB)

    # Connect using environment variable
    print('Connecting to: %s' % SUB_URL)
    subscriber.connect(SUB_URL)

    # -t or --topic will be used to specify a topic
    parser = argparse.ArgumentParser('sub')
    parser.add_argument('--topic', '-t', action='append',
                        help='Specifies a topic to monitor')
    args = parser.parse_args()

    # Setup default topics to use if none specified on command line
    default_topics = [b'CAM1', b'CAM2', b'AUDIO']

    # If args.topic is None then no topics specified on command line
    if args.topic is None:
        topics = default_topics
    else:
        topics = args.topic

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

    try:

        print("Waiting for messages...")

        while True:

            message = subscriber.recv_multipart()

            print('Received: [%s] %s' % (message[0].decode('utf-8'),
                                         message[1].decode('utf-8')))

    except KeyboardInterrupt:
        print("Stopping...")

    finally:

        # Close the subscriber socket
        subscriber.close()

        # Terminate the context
        context.term()


if __name__ == "__main__":
    main()