#!/usr/bin/env python
# coding: utf-8

"""
Runs the model on a recording to detect gunshots
"""

import pickle
import os
import librosa
import sys
sys.path.append("/home/pi/Desktop/yolov3")
from prettytable import PrettyTable
from time import time, sleep
from record import record_to_file
from pub import setup, print_and_pub
from syncClock import now



# Hide Warnings
import warnings
warnings.filterwarnings('ignore')
with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=FutureWarning)
    import numpy as np
    import tensorflow as tf
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 



total_start_time = time()
model_filepath = 'pb_model.pb'
labels = [
            'air_conditioner',
            'car_horn',
            'children_playing',
            'dog_bark',
            'drilling',
            'engine_idling',
            'gun_shot',
            'jackhammer',
            'siren',
            'street_music'
        ]
#print(model_filepath)

# Connect to pub server
publisher = setup()

# Run syncClock
print("Syncing with time server..")
now()


'''
Load trained model.
'''
print('Loading model...')
start_time = time()
graph = tf.Graph()
sess = tf.InteractiveSession(graph = graph)

with tf.gfile.GFile(model_filepath, 'rb') as f:
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(f.read())

#print('Check out the input placeholders:')
nodes = [n.name + ' => ' +  n.op for n in graph_def.node if n.op in ('Placeholder')]

# Define input tensor
model_input = tf.placeholder(tf.float32, shape=[None,40,40,3], name = 'input')
tf.import_graph_def(graph_def, {'input': model_input})
infer_time = time() - start_time
print('Model loading complete!')



# Know your output node name
output_tensor = graph.get_tensor_by_name("import/logits_tensor/BiasAdd:0")
# output = sess.run(output_tensor, feed_dict =  {model_input:  X_test[0:2] })


# # Loading data

## AUDIO DATA PROCESSING
window_size = 512
## This for mel spectogram resolution
n_bands = 60
n_mfcc = 40
n_frames = 40

def windows(data, n_frames):
    ws = window_size * (n_frames - 1)
    start = 0
    while start < len(data):
        yield start, start + ws, ws
        start += (ws / 2)
        ## OVERLAP OF 50%
## END windows


def one_hot_encode(labels, num_class):
    n_labels = len(labels)
    n_unique_labels = num_class
    one_hot_encode = np.zeros((n_labels,n_unique_labels))
    one_hot_encode[np.arange(n_labels), labels] = 1
    return one_hot_encode


def data_processing(work_dir):
    raw_features = []
    _labels = []
    cnt = 0

    #print("Working on dir: ", work_dir)

    for fs in os.listdir(work_dir ):
        if ".wav" not in fs: continue
        sound_clip, sr = librosa.load(work_dir + "/" + fs)
        label = 6
        cnt += 1
        ## Work of file bacthes
        for (start, end, ws) in windows(sound_clip, n_frames):
            ## Get the sound part
            signal = sound_clip[int(start): int(end)]
            if len(signal) == ws:
                mfcc_spec = librosa.feature.mfcc(signal, n_mfcc=n_mfcc, n_mels=n_bands)
                mfcc_spec = mfcc_spec.T.flatten()[:, np.newaxis].T
                raw_features.append(mfcc_spec)
                _labels.append(label)

    print("Loaded ", cnt, " files")
    ## Add a new dimension
    raw_features = np.asarray(raw_features).reshape(len(raw_features), n_mfcc, n_frames, 1)



    ## Concate 2 elements on axis=3
    _features = np.concatenate((raw_features, np.zeros(np.shape(raw_features))), axis=3)

    _features = np.concatenate((_features, np.zeros(np.shape(raw_features))), axis=3)


    for i in range(len(_features)):
        _features[i, :, :, 1] = librosa.feature.delta(order=1, data=_features[i, :, :, 0])
        _features[i, :, :, 2] = librosa.feature.delta(order=2, data=_features[i, :, :, 0])

    # normalize, one-hot data
    test_x = _features
    test_x = test_x.astype('float32')
    test_x /= 255

    test_y = one_hot_encode(np.array(_labels), 10) 
    return test_x, test_y



def predict_label(logits_output):
    predict_y = np.argmax(logits_output, axis = 1)
    return predict_y

def exp_evidence(logits): 
    return np.exp(np.clip(logits,-10,10))

def uncertainty_score( logits_output ):
    evidence = exp_evidence(logits_output)
    alpha = evidence + 1
    u_score = 10 / np.sum(alpha, axis=1, keepdims=True)  # K = num_classes = 10
    return u_score



while True:
    print("Listening...")
    record_start = time()
    record_to_file("sound/input.wav")
    record_time = time() - record_start 

    work_dir = 'sound'
    start_time = time()
    test_x, test_y = data_processing(work_dir)
    load_time = time() - start_time


    # # Testing on loaded model
    start_time = time()
    output = sess.run(output_tensor, feed_dict =  {model_input:  test_x })


    y_pred = predict_label(output)
    uncertainty_y_list = uncertainty_score(output)
    test_time = time() - start_time
    print("Inference time:", infer_time)
    print("Load time:", load_time)
    print("Test time:", test_time)
    print("Total time:", time() - total_start_time - record_time)

    
    t = PrettyTable(['Predict', 'Uncertainty'])
    for i in range(y_pred.shape[0]):
        t.add_row([labels[y_pred[i]], uncertainty_y_list[i][0]])
    print(t)
    
    if len(y_pred) == 2:
        name = labels[y_pred[0]] if uncertainty_y_list[0][0] < uncertainty_y_list[1][0] else labels[y_pred[1]]
    else:
        name = labels[np.argmax(np.bincount(y_pred))]
    total_uncertainty = 1
    for i in range(y_pred.shape[0]):
        if name == labels[y_pred[i]]:
            total_uncertainty *= uncertainty_y_list[i][0]
            
    print("This sound is:", name)
    print_and_pub(publisher, "AUDIO", [name, "AUDIO", now(), round(total_uncertainty, 3)])
    
    print("\n")
    infer_time = 0
    total_start_time = time()
    
    #ans = input("Press enter to continue, q & enter to quit: ")
    #ans = ans.lower()
    #print('\n')
    #if ans == 'q':
        #exit(0)
    #else:
        #infer_time = 0
        #total_start_time = time()
        #continue

