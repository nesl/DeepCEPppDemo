#!/usr/bin/env python
"""
 Copyright (C) 2018-2019 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""
from __future__ import print_function, division

import logging
import os
import sys
from argparse import ArgumentParser, SUPPRESS
from math import exp as exp
from time import time, sleep

import cv2
import numpy as np
from openvino.inference_engine import IENetwork, IEPlugin
from pub import setup, print_and_pub
from syncClock import now



logging.basicConfig(format="[ %(levelname)s ] %(message)s", level=logging.INFO, stream=sys.stdout)
log = logging.getLogger()


def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument("-m", "--model", help="Required. Path to an .xml file with a trained model.",
                      required=True, type=str)
    args.add_argument("-i", "--input", help="Required. Path to a image/video file. (Specify 'cam' to work with "
                                            "camera)", required=True, type=str)
    args.add_argument("-l", "--cpu_extension",
                      help="Optional. Required for CPU custom layers. Absolute path to a shared library with "
                           "the kernels implementations.", type=str, default=None)
    args.add_argument("-pp", "--plugin_dir", help="Optional. Path to a plugin folder", type=str, default=None)
    args.add_argument("-d", "--device",
                      help="Optional. Specify the target device to infer on; CPU, GPU, FPGA, HDDL or MYRIAD is"
                           " acceptable. The sample will look for a suitable plugin for device specified. "
                           "Default value is CPU", default="CPU", type=str)
    args.add_argument("--labels", help="Optional. Labels mapping file", default=None, type=str)
    args.add_argument("-t", "--prob_threshold", help="Optional. Probability threshold for detections filtering",
                      default=0.5, type=float)
    args.add_argument("-iout", "--iou_threshold", help="Optional. Intersection over union threshold for overlapping "
                                                       "detections filtering", default=0.4, type=float)
    args.add_argument("-ni", "--number_iter", help="Optional. Number of inference iterations", default=1, type=int)
    args.add_argument("-pc", "--perf_counts", help="Optional. Report performance counters", default=False,
                      action="store_true")
    args.add_argument("-r", "--raw_output_message", help="Optional. Output inference results raw values showing",
                      default=False, action="store_true")
    return parser


class YoloV3Params:
    # ------------------------------------------- Extracting layer parameters ------------------------------------------
    # Magic numbers are copied from yolo samples
    def __init__(self, param, side):
        self.num = 3 if 'num' not in param else len(param['mask'].split(',')) if 'mask' in param else int(param['num'])
        self.coords = 4 if 'coords' not in param else int(param['coords'])
        self.classes = 80 if 'classes' not in param else int(param['classes'])
        self.anchors = [10.0, 13.0, 16.0, 30.0, 33.0, 23.0, 30.0, 61.0, 62.0, 45.0, 59.0, 119.0, 116.0, 90.0, 156.0,
                        198.0,
                        373.0, 326.0] if 'anchors' not in param else [float(a) for a in param['anchors'].split(',')]
        self.side = side
        if self.side == 13:
            self.anchor_offset = 2 * 6
        elif self.side == 26:
            self.anchor_offset = 2 * 3
        elif self.side == 52:
            self.anchor_offset = 2 * 0
        else:
            assert False, "Invalid output size. Only 13, 26 and 52 sizes are supported for output spatial dimensions"

    def log_params(self):
        params_to_print = {'classes': self.classes, 'num': self.num, 'coords': self.coords, 'anchors': self.anchors}
        [log.info("         {:8}: {}".format(param_name, param)) for param_name, param in params_to_print.items()]


def entry_index(side, coord, classes, location, entry):
    side_power_2 = side ** 2
    n = location // side_power_2
    loc = location % side_power_2
    return int(side_power_2 * (n * (coord + classes + 1) + entry) + loc)


def scale_bbox(x, y, h, w, class_id, confidence, h_scale, w_scale):
    xmin = int((x - w / 2) * w_scale)
    ymin = int((y - h / 2) * h_scale)
    xmax = int(xmin + w * w_scale)
    ymax = int(ymin + h * h_scale)
    return dict(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, class_id=class_id, confidence=confidence)


def parse_yolo_region(blob, resized_image_shape, original_im_shape, params, threshold):
    # ------------------------------------------ Validating output parameters ------------------------------------------
    _, _, out_blob_h, out_blob_w = blob.shape
    assert out_blob_w == out_blob_h, "Invalid size of output blob. It sould be in NCHW layout and height should " \
                                     "be equal to width. Current height = {}, current width = {}" \
                                     "".format(out_blob_h, out_blob_w)

    # ------------------------------------------ Extracting layer parameters -------------------------------------------
    orig_im_h, orig_im_w = original_im_shape
    resized_image_h, resized_image_w = resized_image_shape
    objects = list()
    predictions = blob.flatten()
    side_square = params.side * params.side

    # ------------------------------------------- Parsing YOLO Region output -------------------------------------------
    for i in range(side_square):
        row = i // params.side
        col = i % params.side
        for n in range(params.num):
            obj_index = entry_index(params.side, params.coords, params.classes, n * side_square + i, params.coords)
            scale = predictions[obj_index]
            if scale < threshold:
                continue
            box_index = entry_index(params.side, params.coords, params.classes, n * side_square + i, 0)
            x = (col + predictions[box_index + 0 * side_square]) / params.side * resized_image_w
            y = (row + predictions[box_index + 1 * side_square]) / params.side * resized_image_h
            # Value for exp is very big number in some cases so following construction is using here
            try:
                w_exp = exp(predictions[box_index + 2 * side_square])
                h_exp = exp(predictions[box_index + 3 * side_square])
            except OverflowError:
                continue
            w = w_exp * params.anchors[params.anchor_offset + 2 * n]
            h = h_exp * params.anchors[params.anchor_offset + 2 * n + 1]
            for j in range(params.classes):
                class_index = entry_index(params.side, params.coords, params.classes, n * side_square + i,
                                          params.coords + 1 + j)
                confidence = scale * predictions[class_index]
                if confidence < threshold:
                    continue
                objects.append(scale_bbox(x=x, y=y, h=h, w=w, class_id=j, confidence=confidence,
                                          h_scale=orig_im_h / resized_image_h, w_scale=orig_im_w / resized_image_w))
    return objects


def intersection_over_union(box_1, box_2):
    width_of_overlap_area = min(box_1['xmax'], box_2['xmax']) - max(box_1['xmin'], box_2['xmin'])
    height_of_overlap_area = min(box_1['ymax'], box_2['ymax']) - max(box_1['ymin'], box_2['ymin'])
    if width_of_overlap_area < 0 or height_of_overlap_area < 0:
        area_of_overlap = 0
    else:
        area_of_overlap = width_of_overlap_area * height_of_overlap_area
    box_1_area = (box_1['ymax'] - box_1['ymin']) * (box_1['xmax'] - box_1['xmin'])
    box_2_area = (box_2['ymax'] - box_2['ymin']) * (box_2['xmax'] - box_2['xmin'])
    area_of_union = box_1_area + box_2_area - area_of_overlap
    if area_of_union == 0:
        return 0
    return area_of_overlap / area_of_union


def main():
    args = build_argparser().parse_args()

    model_xml = args.model
    model_bin = os.path.splitext(model_xml)[0] + ".bin"
    
    # ------------- 0. Setting up pub/sub and GoodClock -------------
    # Connect to pub server
    publisher = setup()

    # Run syncClock
    print("Syncing with time server..")
    now()


    # ------------- 1. Plugin initialization for specified device and load extensions library if specified -------------
    plugin = IEPlugin(device=args.device, plugin_dirs=args.plugin_dir)
    if args.cpu_extension and 'CPU' in args.device:
        plugin.add_cpu_extension(args.cpu_extension)

    # -------------------- 2. Reading the IR generated by the Model Optimizer (.xml and .bin files) --------------------
    log.info("Loading network files:\n\t{}\n\t{}".format(model_xml, model_bin))
    net = IENetwork(model=model_xml, weights=model_bin)

    # ---------------------------------- 3. Load CPU extension for support specific layer ------------------------------
    if plugin.device == "CPU":
        supported_layers = plugin.get_supported_layers(net)
        not_supported_layers = [l for l in net.layers.keys() if l not in supported_layers]
        if len(not_supported_layers) != 0:
            log.error("Following layers are not supported by the plugin for specified device {}:\n {}".
                      format(plugin.device, ', '.join(not_supported_layers)))
            log.error("Please try to specify cpu extensions library path in sample's command line parameters using -l "
                      "or --cpu_extension command line argument")
            sys.exit(1)

    assert len(net.inputs.keys()) == 1, "Sample supports only YOLO V3 based single input topologies"
    assert len(net.outputs) == 3, "Sample supports only YOLO V3 based triple output topologies"

    # ---------------------------------------------- 4. Preparing inputs -----------------------------------------------
    log.info("Preparing inputs")
    input_blob = next(iter(net.inputs))

    #  Defaulf batch_size is 1
    net.batch_size = 1

    # Read and pre-process input images
    n, c, h, w = net.inputs[input_blob].shape

    if args.labels:
        with open(args.labels, 'r') as f:
            labels_map = [x.strip() for x in f]
    else:
        labels_map = None

    input_stream = 0 if args.input == "cam" else args.input

    is_async_mode = True
    cap = cv2.VideoCapture(input_stream)
    number_input_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    number_input_frames = 1 if number_input_frames != -1 and number_input_frames < 0 else number_input_frames
    
    cap.set(3, 1280) # Set the resolution width
    cap.set(4, 720)  # Set the resolution height
    cap.set(10, 135) # Brightness
    cap.set(11, 118) # Contrast
    cap.set(12, 180) # Saturation
    
    autoFocus = True
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    log.info("Initial camera settings:")
    print("\tBrightness: ", cap.get(10))
    print("\tContrast: ", cap.get(11))
    print("\tSaturation: ", cap.get(12))
    print("\tGain: ", cap.get(14))
    print("\tExposure: ", cap.get(15))
    print("\tFocus: ", cap.get(28))
    """
    cap.set(3 , 640  ) # width        
    cap.set(4 , 480  ) # height       
    cap.set(10, 120  ) # brightness     min: 0   , max: 255 , increment:1, default:128
    cap.set(11, 50   ) # contrast       min: 0   , max: 255 , increment:1, default:128   
    cap.set(12, 70   ) # saturation     min: 0   , max: 255 , increment:1, default:128
    cap.set(13, 13   ) # hue            NOT SUPPORTED 
    cap.set(14, 50   ) # gain           min: 0   , max: 127 , increment:1, CHANGES AUTOMATICALLY
    cap.set(15, -3   ) # exposure       min: -7  , max: -1  , increment:1, CHANGES AUTOMATICALLY
    cap.set(17, 5000 ) # white_balance  min: 4000, max: 7000, increment:1, NOT SUPPORTED 
    cap.set(28, 0    ) # focus          min: 0   , max: 255 , increment:5, CHANGES AUTOMATICALLY
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Turn autofocus on or off
    """
    sleep(2)
    
    wait_key_code = 1

    # Number of frames in picture is 1 and this will be read in cycle. Sync mode is default value for this case
    if number_input_frames != 1:
        ret, frame = cap.read()
    else:
        is_async_mode = False
        wait_key_code = 0

    # ----------------------------------------- 5. Loading model to the plugin -----------------------------------------
    log.info("Loading model to the plugin")
    exec_net = plugin.load(network=net, num_requests=2)

    cur_request_id = 0
    next_request_id = 1
    det_time = 0
    parsing_time = 0
    filter_time = 0
    render_time = 0
    
    
    # ----------------------------------------------- 6. Doing inference -----------------------------------------------
    print("To close the application, press 'CTRL+C' or any key with focus on the output window")
    showVideoFeed = True
    showCameraInfo = True
    showTimes = False
    runYOLO = True
    while cap.isOpened():
        if showCameraInfo:
            print("Gain: ", cap.get(14))
            print("Exposure: ", cap.get(15))
            print("Focus: ", cap.get(28))
        
        
        # Here is the first asynchronous point: in the Async mode, we capture frame to populate the NEXT infer request
        # in the regular mode, we capture frame to the CURRENT infer request
        if is_async_mode:
            ret, next_frame = cap.read()
        else:
            ret, frame = cap.read()

        if not ret:
            break

        if is_async_mode:
            request_id = next_request_id
            in_frame = cv2.resize(next_frame, (w, h))
        else:
            request_id = cur_request_id
            in_frame = cv2.resize(frame, (w, h))

        if runYOLO:
            # resize input_frame to network size
            in_frame = in_frame.transpose((2, 0, 1))  # Change data layout from HWC to CHW
            in_frame = in_frame.reshape((n, c, h, w))

            # Start inference
            start_time = time()
            exec_net.start_async(request_id=request_id, inputs={input_blob: in_frame})
            det_time = time() - start_time
            #print(det_time, end=",")

            # Collecting object detection results
            objects = list()
            if exec_net.requests[cur_request_id].wait(-1) == 0:
                output = exec_net.requests[cur_request_id].outputs
                

                start_time = time()
                for layer_name, out_blob in output.items():
                    layer_params = YoloV3Params(net.layers[layer_name].params, out_blob.shape[2])
                    if args.raw_output_message:
                        log.info("Layer {} parameters: ".format(layer_name))
                        layer_params.log_params()
                    objects += parse_yolo_region(out_blob, in_frame.shape[2:],
                                                 frame.shape[:-1], layer_params,
                                                 args.prob_threshold)
                parsing_time = time() - start_time
                #print(parsing_time, end=",")

            start_time = time()
            # Filtering overlapping boxes with respect to the --iou_threshold CLI parameter
            """
            objects: List of dicts. [{'confidence', 'class_id', 'xmin', 'ymin', 'ymax', 'xmax'}, .. ]
            class_id: 2 = car, 7 = truck
            """
            for i in range(len(objects)):
                if objects[i]['confidence'] == 0:
                    continue
                for j in range(i + 1, len(objects)):
                    if intersection_over_union(objects[i], objects[j]) > args.iou_threshold:
                        objects[j]['confidence'] = 0
                        
            filter_time = time() - start_time
            #print(filter_time)
            # Drawing objects with respect to the --prob_threshold CLI parameter
            objects = [obj for obj in objects if obj['confidence'] >= args.prob_threshold]

            if len(objects) and args.raw_output_message:
                log.info("\nDetected boxes for batch {}:".format(1))
                log.info(" Class ID | Confidence | XMIN | YMIN | XMAX | YMAX | COLOR ")

            origin_im_size = frame.shape[:-1]
            for obj in objects:
                # Validation bbox of detected object
                if obj['xmax'] > origin_im_size[1] or obj['ymax'] > origin_im_size[0] or obj['xmin'] < 0 or obj['ymin'] < 0:
                    continue
                color = (int(min(obj['class_id'] * 12.5, 255)),
                         min(obj['class_id'] * 7, 255), min(obj['class_id'] * 5, 255))
                det_label = labels_map[obj['class_id']] if labels_map and len(labels_map) >= obj['class_id'] else \
                    str(obj['class_id'])

                if args.raw_output_message:
                    log.info(
                        "{:^9} | {:10f} | {:4} | {:4} | {:4} | {:4} | {} ".format(det_label, obj['confidence'], obj['xmin'],
                                                                                  obj['ymin'], obj['xmax'], obj['ymax'],
                                                                                  color))           
                
                # Check for Red Truck
                if det_label == "truck":
                    crop = frame[obj['ymin']:obj['ymax'], obj['xmin']:obj['xmax']].copy()
                    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
                    
                    # Range for lower
                    lower_red = np.array([0,50,20])
                    upper_red = np.array([15,255,255])
                    mask1 = cv2.inRange(hsv, lower_red, upper_red)
                    
                    # Range for upper
                    lower_red = np.array([160,50,20])
                    upper_red = np.array([180,255,255])
                    mask2 = cv2.inRange(hsv,lower_red,upper_red)
                    
                    red_mask = mask1 + mask2
                    #cv2.imshow('red_mask', red_mask)
                    #cv2.waitKey(0)
                    #cv2.destroyAllWindows()
                    ratio = cv2.countNonZero(red_mask)/(crop.size/3)
                    print('Red pixel percentage:', np.round(ratio*100, 2))
                    if ratio >= 0.13:
                        det_label = "red_truck" 
                    
                if showVideoFeed:
                    cv2.rectangle(frame, (obj['xmin'], obj['ymin']), (obj['xmax'], obj['ymax']), color, 2)
                        
                    cv2.putText(frame,
                        "#" + det_label + ' ' + str(round(obj['confidence'] * 100, 1)) + ' %',
                        (obj['xmin'], obj['ymin'] - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 1)
                    
                print_and_pub(publisher, "CAM1", [det_label, "CAM1", now(), round(obj['confidence'], 3)])
                
            
            key = -1
            if showVideoFeed:
                # Draw performance stats over frame
                inf_time_message = "Inference time: N\A for async mode" if is_async_mode else \
                    "Inference time: {:.3f} ms".format(det_time * 1e3)
                render_time_message = "OpenCV rendering time: {:.3f} ms".format(render_time * 1e3)
                async_mode_message = "Async mode is on. Processing request {}".format(cur_request_id) if is_async_mode else \
                    "Async mode is off. Processing request {}".format(cur_request_id)
                parsing_message = "YOLO parsing time is {:.3f}".format(parsing_time * 1e3)

                cv2.putText(frame, inf_time_message, (15, 15), cv2.FONT_HERSHEY_COMPLEX, 0.5, (200, 10, 10), 1)
                cv2.putText(frame, render_time_message, (15, 45), cv2.FONT_HERSHEY_COMPLEX, 0.5, (10, 10, 200), 1)
                cv2.putText(frame, async_mode_message, (10, int(origin_im_size[0] - 20)), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                            (10, 10, 200), 1)
                cv2.putText(frame, parsing_message, (15, 30), cv2.FONT_HERSHEY_COMPLEX, 0.5, (10, 10, 200), 1)

                start_time = time()
                cv2.imshow("DetectionResults", frame)
                render_time = time() - start_time
                
        elif showVideoFeed:
            cv2.imshow("DetectionResults", frame)


        if is_async_mode:
            cur_request_id, next_request_id = next_request_id, cur_request_id
            frame = next_frame

        key = cv2.waitKey(wait_key_code)
        
        if showTimes:
            print("Inference Time:", det_time)
            print("Parsing Time:", parsing_time)
            print("Filter Time:", filter_time)
            print("Render Time:", render_time)
            print("Total Time:", det_time + parsing_time + filter_time + render_time, end="\n\n")
        else:
            print("\n")


        # ESC key
        if key == 27:
            break
            
        # Tab key
        if key == 9:
            exec_net.requests[cur_request_id].wait()
            is_async_mode = not is_async_mode
            log.info("Switched to {} mode".format("async" if is_async_mode else "sync"))
        
        # 'a' Key - Toggle Autofocus
        if key == 65 or key == 97:
            if autoFocus:
                log.info("Autofocus off")
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                autoFocus = False
            else:
                log.info("Autofocus on")
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                autoFocus = True
                
        # 'f' Key - Set focus to 30 (Good for tablets)
        if key == 102 or key == 70:
            cap.set(28, 30)
            log.info("Set focus to 30")
            
        # 's' Key - Decrement focus by 5
        if (key == 83 or key == 115) and cap.get(28) - 5 >= 0:
            cap.set(28, cap.get(28) - 5)
            log.info("Set focus to {}".format(cap.get(28)))
            
        # 'd' Key - Increment focus by 5
        if (key == 68 or key == 100) and cap.get(28) + 5 <= 255:
            cap.set(28, cap.get(28) + 5)
            log.info("Set focus to {}".format(cap.get(28)))
        
        # 'c' Key - Closes the live view, CANNOT BE TURNED BACK ON
        if (key == 67 or key == 99) and runYOLO:
            log.info("Closing the live view")
            cv2.destroyAllWindows()
            render_time = 0
            showVideoFeed = False
            
        # 'h' Key - Toggles the camera Info
        if key == 72 or key == 104:
            if showCameraInfo:
                log.info("Hiding camera information")
                showCameraInfo = False
            else:
                log.info("Showing camera information")
                showCameraInfo = True
        
        # 't' Key - Toggles Times
        if key == 84 or key == 116:
            if showTimes:
                log.info("Hiding times")
                showTimes = False
            else:
                log.info("Showing times")
                showTimes = True
        
        # 'n' Key - Toggle YOLO
        if key == 78 or key == 110:
            if runYOLO:
                log.info("Stopping YOLOv3")
                runYOLO = False
            else:
                log.info("Running YOLOv3")
                runYOLO = True
            
            
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    sys.exit(main() or 0)
