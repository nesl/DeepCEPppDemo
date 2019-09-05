from server import *
ce = 'coordinated_attack'
# proxy_IP = '127.0.0.1'
proxy_IP = "192.168.8.224"
proxy_URL = "tcp://" + proxy_IP + ":2222"
sending_CE = False

deepcep_server(proxy_URL, ce, sending_CE=sending_CE, diagnose = False)
