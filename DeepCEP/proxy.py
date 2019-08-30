import zmq

SUB_URL = "tcp://*:1111"
PUB_URL = "tcp://*:2222"


def main():
    
    # Create a ZMQ Context
    context = zmq.Context()

    # Create frontend spcket
    frontend = context.socket(zmq.SUB)
    frontend.bind(SUB_URL)
    frontend.setsockopt(zmq.SUBSCRIBE, b"")

    # Create backend socket
    backend = context.socket(zmq.PUB)
    backend.bind(PUB_URL)

    # Create Proxy
    try:
      zmq.proxy(frontend, backend)
    finally:
      frontend.close()
      backend.close()
      context.term()


if __name__ == "__main__":
    main()
