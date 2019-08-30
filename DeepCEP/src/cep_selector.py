import numpy as np
from problog.program import PrologString
from problog import get_evaluatable

"""
the module should have:
input: events with attributes(timestamp, values)
output: the probability of this event seqence being a Complex Event
"""

# def Selector(event_time, event_value, diagnose = 0):
def Selector(path_i_events, ce, diagnose = 0):
    
    if ce == 'coordinated_attack':
        # selector model for hard-coded coordinated attack
        constriant1 = ( path_i_events[1][2] - path_i_events[0][2]<= 100 )
        constriant2 = ( path_i_events[2][2] - path_i_events[1][2]<= 200 )
        ce_event = constriant1 and constriant2
    elif ce == 'convoy':
        # time
        constriant1 = ( path_i_events[1][2] - path_i_events[0][2]<= 100 )
        constriant2 = ( path_i_events[3][2] - path_i_events[2][2]<= 100 )
        constriant3 = ( path_i_events[2][2] - path_i_events[1][2]<= 200 )
        # location
        constriant4 = ( path_i_events[0][1] == 'CAM1' )
        constriant5 = ( path_i_events[1][1] == 'CAM1' )
        constriant6 = ( path_i_events[2][1] == 'CAM2' )
        constriant7 = ( path_i_events[3][1] == 'CAM2' )
        ce_event = constriant1 and constriant2 and constriant3 and constriant4 and constriant5 and constriant6 and constriant7

        
        
        
        
#     # definition of Selector model
#     selector_model = """
#     event(a, a_time, a_value).
#     event(b, b_time, b_value).
#     event(c, c_time, c_value).
#     % compare_time(A, B, SIGN) :- event(A,TA, VA), event(B,TB, VB), SIGN is sign(TA-TB).
#     % % if SIGN is zero, then TA == TB, if 1, TA> TB; if -1, TA<TB
#     % compare_value(A, B, SIGN) :- event(A,TA, VA), event(B,TB, VB), SIGN is sign(VA-VB).
#     compare(A, B, value, SIGN) :- event(A,TA, VA), event(B,TB, VB), SIGN is sign(VA-VB).
#     compare(A, B, time, SIGN) :- event(A,TA, VA), event(B,TB, VB), SIGN is sign(TA-TB).
#     time_satisfy:-compare(c,b,time,1), compare(b,a,time,1).
#     value_satisfy:-compare(c,b,value,0), compare(b,a,value, 0).
#     ce_event:- time_satisfy, value_satisfy.
#     % query(event(_,_,_)).
#     query(time_satisfy).
#     query(value_satisfy).
#     query(ce_event).
#     """

#     selector_model= selector_model.replace('a_time', str(event_time[0] ) )
#     selector_model= selector_model.replace('b_time', str(event_time[1]) )
#     selector_model= selector_model.replace('c_time', str(event_time[2]) )
#     selector_model= selector_model.replace('a_value', str(event_value[0]) )
#     selector_model= selector_model.replace('b_value', str(event_value[1]) )
#     selector_model= selector_model.replace('c_value', str(event_value[2] ) )

    
#     result = get_evaluatable().create_from(PrologString(selector_model)).evaluate()
    
#     # naive way of getting ProbLog inference result
#     py_result = {}
#     for i in result:
#         py_result[str(i)] = result[i]
    
#     condition_satisfy = np.array([py_result['time_satisfy'], py_result['value_satisfy']])
#     ce_event = np.array([py_result['ce_event']] )

#     if diagnose:
# #         print(selector_model, '\n')
#         print('============================================')
#         print(result, '\n')
#         print('Event time: \t',event_time, '\nEvent value: \t', event_value)
#         # print the reuslt:
#         print('Satisfied(time/value): \t',condition_satisfy,
#               '\nComplexEvent: \t',ce_event)
#         print('\n')

    return ce_event
