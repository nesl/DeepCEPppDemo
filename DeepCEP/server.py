# import socket
# import threading
import time
import sys

import pickle

import numpy as np

    
# import argparse
# import time
import zmq
# from pprint import pprint
# import pickle


from src.cep_definition import *
from src.cep_es_stack import *
from src.cep_FSM import *
from src.cep_utils import *
from src.cep_selector import *

def setup(PUB_URL):
    # Create a ZMQ Context
    context = zmq.Context()
	
	# Create a publisher socket
    publisher = context.socket(zmq.PUB)
    
    # Connect
    print ("Sending to Proxy: %s" % PUB_URL)
    publisher.connect(PUB_URL)
    
    return publisher


def socket_service(server_ip, ce, target_ip, diagnose = False):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # check if port is taken（socket.error: [Errno 98] Address already in use）
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((server_ip, 6666)) # server_ip: the ip address binds to current server
        s.listen(10)
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    print ('Waiting connection...')

    ## read in CEP query and create CEP model
    ce_path = ce+'.txt'
    print ('Reading Complex Event definition from: ', ce_path)
    ce_def = read_ce_def(ce_path)
    combine_format, events, constraints, time_win = ce_def_parsing(ce_def)
    
#     event_info, state_info, state_num = seq_info_extraction(events)
    event_info, state_info, state_num, uniq_event, event_dict, pattern_without_flag, without_info = seq_info_extraction(events)
    
    # need to inject initial state 'e0' to state_info
    #  add initial state e0 to the state_info.
    state_info.insert(0, 'e0')
    state_num = state_num+1
    
    
    print("event_info: ",event_info)
    print("unique_event: ",uniq_event)
    print("state_info: ",state_info)
    print("state_num: ",state_num)

    if combine_format == 'SEQ':
        pattern_detect_model = create_FSM_problog(state_info, event_info, uniq_event, consecutive = True)
        seq_flag = True
    elif combine_format == 'PATTERN':
        pattern_detect_model = create_FSM_problog(state_info, event_info, uniq_event, consecutive = False)
        seq_flag = False 

        
    print('Sequence flag: ', seq_flag)
    print('\n============ProbLog model: ============\n')
    print(pattern_detect_model)
    print('\n============ProbLog model Finished ============\n')
    
    ## create event dictionary based on the order of unique events
    # the dont_care event is not in the dictionary, 
    # but it should be coded as [0 0 0 ... 1]
    event_dict = event_encoding_dict(uniq_event)

    
    ## create run-time event stack
    ## stact update rule is associated with stack 
    stored_e_num = 10
    event_stack = create_event_stack(state_num, stored_e_num)
    if diagnose: 
        print('\n============Initial Event Stack==============\n')
        print('event_stack_shape: ',event_stack.shape)
        print(event_stack)
        print('Event Dict: ')
        print(event_dict)
        event_dict
    
    while True:
        conn, addr = s.accept()
        t = threading.Thread(target=deal_data, 
                             args=(conn, addr, 
                                   state_num, event_dict, 
                                   pattern_detect_model,
                                   state_info, uniq_event,
                                   stored_e_num,
                                   event_stack,
                                   seq_flag,
                                   ce, target_ip,
                                   diagnose))
        t.start()

        
        
def deal_data_org(conn, addr, 
              state_num, event_dict, 
              pattern_detect_model, 
              state_info, uniq_event,
              stored_e_num,
              event_stack,
              seq_flag,
              ce, target_ip,
              diagnose = False):
    
    print ('Accept new connection from {0}'.format(addr) )
    # send welcome msg to the client side.
    conn.send('Hi, Welcome to the server!'.encode()) 
    
    # initialization:
    # create ce_buffer to store all the K events
    # the ce_buffer is updated as queue:  append(new_e), and pop(0)
    ce_buffer = [None for i in range(stored_e_num)]
    current_state = one_hot_id(state_num, 0) # initial state is zero state(final state)
    if diagnose:  
        print('ce_buffer: ',ce_buffer)
        print("current_state: ",current_state)
    
    
    # preparing for sending CE
    if target_ip != None:
        try:
            s_ce = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         s.connect(('172.17.43.10', 6666))
            s_ce.connect((target_ip, 6666))  # the IP destination for sending CE to
        except socket.error as msg:
            print (msg)
            sys.exit(1)
        print (s_ce.recv(1024).decode())
    
    
    
    # keep listening to data from device, and perform CEP
    while True:
        data = conn.recv(1024)
        data = pickle.loads(data) # decode data
        print ('Receiving data from: {0}'.format(addr, data ) )
        print('Event_type \t Sensor_ID \t Event_time\t Uncertainty')
        print('%s \t\t %s \t\t %2f \t\t %.2f \n' %(data[0], data[1], data[2], data[3]))

        # encode event
        current_input = event2vec(data[0], event_dict)
        
        # update event buffer:
        ce_buffer.pop(0)
        ce_buffer.append(data)
        
        # update the event stack: move the event states left for 1 timestep
        # keep the first init event states
        update_stack(event_stack,seq_flag = seq_flag)

        current_states = event_stack[:, -2]

        event_stack[:, -1] = states_update(pattern_detect_model, 
                                           state_info, uniq_event,
                                           current_states, current_input,
                                           seq_flag = seq_flag,
                                           overlap_flag = True,
                                           diagnose = diagnose)
        # the overlapping flag is controlled in the state_update process
        # overlap_flag = True by default
        
        if diagnose: 
            print('\nThe updated event states stack: ')
            print(event_stack)
            print('\nThe updated event buffer: ')
            print(ce_buffer)
        
        # if CE detected :
        if event_stack[-1, -1] != 0:
            print("Finding the satisfied sequences...")
            ce_candidate_idx = sequence_search(event_stack)
            # print the path and index of events
            if diagnose: 
                print(ce_candidate_idx)
                print(ce_buffer)
            for path_i in ce_candidate_idx:
#                 if diagnose: 
#                     for path_i_idx_i in path_i:
#                         print(ce_buffer[int(path_i_idx_i-1)])
                    
                ############ add selector model here ######
                path_i_events = [ce_buffer[int(i-1)] for i in path_i]
                ce_event_flag = Selector(path_i_events, ce = ce, diagnose = diagnose)
#                 ce_event_flag = 1

                # print( ce_event_flag)
                if ce_event_flag == 1:
                    print("========Complex Event detected!========")
                    print("=========== CEvent: ", ce, " ==========")
                    print("Event \t\t\t Time \t\t\t Uncertainty")
                    
                    ce_uncertainty = 1
                    for path_idx in path_i:
                        print(ce_buffer[int(path_idx-1)][0], "\t\t", ce_buffer[int(path_idx-1)][2], "\t\t", ce_buffer[int(path_idx-1)][3])
                        ce_uncertainty = ce_uncertainty *ce_buffer[int(path_idx-1)][3]
#                     print(ce_buffer[int(path_i[1]-1)][0], "\t\t", ce_buffer[int(path_i[1]-1)][2], "\t\t", ce_buffer[int(path_i[0]-1)][3])
#                     print(ce_buffer[int(path_i[2]-1)][0], "\t\t", ce_buffer[int(path_i[2]-1)][2], "\t\t", ce_buffer[int(path_i[0]-1)][3])
                    
                    print("CE Uncertainty: %.3f"%ce_uncertainty)
#                     print("Time\t %.2f \t %.2f \t %.2f "\
#                           %(ce_buffer[int(path_i[0]-1)][2],
#                             ce_buffer[int(path_i[1]-1)][2],
#                             ce_buffer[int(path_i[2]-1)][2]))
#                     print("Event\t %s \t %s \t %s \t "\
#                           %(ce_buffer[int(path_i[0]-1)][0],
#                             ce_buffer[int(path_i[1]-1)][0],
#                             ce_buffer[int(path_i[2]-1)][0])
#                          )

#                     print("Time: %2f, %2f, %2f." 
#                           %(event_time[0], event_time[1], event_time[2]))
    #                         print("Subject ID: %d" %event_value[0])
                    print("=======================================\n")
                    
                    if target_ip != None:
                        # generating hierarchical complex events.
                        print("Generating event: ")
                        ce_event = ['convoy', 0, ce_buffer[int(path_i[2]-1)][2], ce_uncertainty]  # event type, sid, event time
                        print("sending: ", ce_event)
                        data=pickle.dumps(ce_event)
                        s_ce.send(data)

    # closing connection.
        #time.sleep(1)
        if data[0] == 'exit' or not data:
            print ('{0} connection close'.format(addr) )
            conn.send('Connection closed!'.encode())
            break

    conn.close()

    
def deal_data(subscriber, 
              state_num, event_dict, 
              pattern_detect_model, 
              state_info, uniq_event,
              stored_e_num,
              event_stack,
              seq_flag,
              ce, ce_publisher,sending_CE,
              diagnose = False):
    
    # initialization:
    # create ce_buffer to store all the K events
    # the ce_buffer is updated as queue:  append(new_e), and pop(0)
    ce_buffer = [None for i in range(stored_e_num)]
    current_state = one_hot_id(state_num, 0) # initial state is zero state(final state)
    if diagnose:  
        print('ce_buffer: ',ce_buffer)
        print("current_state: ",current_state)
    
    # keep listening to data from device, and perform CEP
    while True:
        
        message = subscriber.recv_multipart()
        topic = message[0].decode('utf-8')
        data = pickle.loads(message[1])
        print('Received: ', topic, data)

        print('Event_type \t Sensor_ID \t Event_time\t Uncertainty')
        print('%s \t\t %s \t\t %2f \t\t %.2f \n' %(data[0], data[1], data[2], data[3]))

        # encode event
        current_input = event2vec(data[0], event_dict)
        
        # update event buffer:
        ce_buffer.pop(0)
        ce_buffer.append(data)
        
        # update the event stack: move the event states left for 1 timestep
        # keep the first init event states
        update_stack(event_stack,seq_flag = seq_flag)

        current_states = event_stack[:, -2]

        event_stack[:, -1] = states_update(pattern_detect_model, 
                                           state_info, uniq_event,
                                           current_states, current_input,
                                           seq_flag = seq_flag,
                                           overlap_flag = True,
                                           diagnose = diagnose)
        # the overlapping flag is controlled in the state_update process
        # overlap_flag = True by default
        
        if diagnose: 
            print('\nThe updated event states stack: ')
            print(event_stack)
            print('\nThe updated event buffer: ')
            print(ce_buffer)
        
        # if CE detected :
        if event_stack[-1, -1] != 0:
            print("Finding the satisfied sequences...")
            ce_candidate_idx = sequence_search(event_stack)
            # print the path and index of events
            if diagnose: 
                print(ce_candidate_idx)
                print(ce_buffer)
            for path_i in ce_candidate_idx:
                    
                ############ add selector model here ######
                path_i_events = [ce_buffer[int(i-1)] for i in path_i]
                ce_event_flag = Selector(path_i_events, ce = ce, diagnose = diagnose)
#                 ce_event_flag = 1

                # print( ce_event_flag)
                if ce_event_flag == 1:
                    print("========Complex Event detected!========")
                    print("=========== CEvent: ", ce, " ==========")
                    print("Event \t\t Time \t\t Uncertainty")
                    
                    ce_uncertainty = 1
                    for path_idx in path_i:
                        print(ce_buffer[int(path_idx-1)][0], "\t\t", ce_buffer[int(path_idx-1)][2], "\t\t", ce_buffer[int(path_idx-1)][3])
                        ce_uncertainty = ce_uncertainty *ce_buffer[int(path_idx-1)][3]

                    print("CE Uncertainty: %.3f"%ce_uncertainty)
                    print("=======================================\n")
                    
                    
                    if sending_CE == True:
                        # generating hierarchical complex events.
                        print("Generating event: ")
                        ce_event = ['convoy', 'CE_CONVOY', ce_buffer[int(path_i[3]-1)][2], ce_uncertainty]  # event type, sid, event time
                        data_ce=pickle.dumps(ce_event)

                        ce_topic = 'CE_CONVOY'
                        btopic = ce_topic.encode('utf-8')
                        ce_publisher.send_multipart([btopic, data_ce])
                        print("sending: ", "[%s] "%ce_topic, ce_event)


        if data[0] == 'exit' or not data:
            print ('connection close' )
            break

    
    
def deepcep_server(proxy_URL, ce, sending_CE=False, diagnose = False):
    
    # ==========First read-in CE definition =========
    ## read in CEP query and create CEP model
    ce_path = ce+'.txt'
    print ('Reading Complex Event definition from: ', ce_path)
    ce_def = read_ce_def(ce_path)
    combine_format, events, constraints, time_win = ce_def_parsing(ce_def)
    
#     event_info, state_info, state_num = seq_info_extraction(events)
    event_info, state_info, state_num, uniq_event, event_dict, pattern_without_flag, without_info = seq_info_extraction(events)
    
    # need to inject initial state 'e0' to state_info
    #  add initial state e0 to the state_info.
    state_info.insert(0, 'e0')
    state_num = state_num+1
     
    print("event_info: ",event_info)
    print("unique_event: ",uniq_event)
    print("state_info: ",state_info)
    print("state_num: ",state_num)

    if combine_format == 'SEQ':
        pattern_detect_model = create_FSM_problog(state_info, event_info, uniq_event, consecutive = True)
        seq_flag = True
    elif combine_format == 'PATTERN':
        pattern_detect_model = create_FSM_problog(state_info, event_info, uniq_event, consecutive = False)
        seq_flag = False 
        
    print('Sequence flag: ', seq_flag)
    print('\n============ProbLog model: ============\n')
    print(pattern_detect_model)
    print('\n============ProbLog model Finished ============\n')
    
    ## create event dictionary based on the order of unique events
    # the dont_care event is not in the dictionary, 
    # but it should be coded as [0 0 0 ... 1]
    event_dict = event_encoding_dict(uniq_event)

    ## create run-time event stack
    ## stact update rule is associated with stack 
    stored_e_num = 1000
    event_stack = create_event_stack(state_num, stored_e_num)
    if diagnose: 
        print('\n============Initial Event Stack==============\n')
        print('event_stack_shape: ',event_stack.shape)
        print(event_stack)
        print('Event Dict: ')
        print(event_dict)
        event_dict

    
    # ==========Next create publisher if necessary =========
    if sending_CE:
        pub_URL = proxy_URL.replace('2222', '1111')

        ce_publisher = setup(pub_URL)
    else: 
        ce_publisher = None
    
    
    # ==========Then subscribe to topics related to CE =========
    # Create a ZMQ Context
    context = zmq.Context()

    # Create a subscriber socket
    subscriber = context.socket(zmq.SUB)

    # Connect using environment variable
    print('Listening to Proxy: %s' % proxy_URL)
    subscriber.connect(proxy_URL)

#     # -t or --topic will be used to specify a topic
#     parser = argparse.ArgumentParser('sub')
#     parser.add_argument('--topic', '-t', action='append',
#                         help='Specifies a topic to monitor')
#     args = parser.parse_args()
    if ce == 'coordinated_attack':
        topics = [b'AUDIO', b'CE_CONVOY', b'MARC_EC']
    elif ce == 'convoy':
        topics = [b'CAM1', b'CAM2']


    # Setup default topics to use if none specified on command line
    default_topics = [b'CAM1', b'CAM2', b'AUDIO']

    # If args.topic is None then no topics specified on command line
    if topics is None:
        topics = default_topics
    else:
        topics = topics

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
        # ========== When receiving message, perform CEP =========
        deal_data(subscriber, 
                  state_num, event_dict, 
                  pattern_detect_model, 
                  state_info, uniq_event,
                  stored_e_num,
                  event_stack,
                  seq_flag,
                  ce, ce_publisher, sending_CE = sending_CE, 
                  diagnose = diagnose)
        
        
        
#     try:
#         # ========== When receiving message, perform CEP =========
#         print("Waiting for messages...")
#         while True:
    
#             message = subscriber.recv_multipart()
#             topic = message[0].decode('utf-8')
#             event_list = pickle.loads(message[1])
#             print('Received: ', topic, event_list)
            

            
    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        # Close the subscriber socket
        subscriber.close()
        # Terminate the context
        context.term()





if __name__ == '__main__':
    ce = 'coordinated_attack'
    proxy_IP = '127.0.0.1'
    proxy_URL = "tcp://" + proxy_IP + ":2222"
    sending_CE = False
    
    deepcep_server(proxy_URL, ce, sending_CE=sending_CE, diagnose = False)
