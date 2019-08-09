import os
import sys
import cv2
import numpy as np
from shutil import copy2, rmtree
from pydarknet import Detector, Image
"""
Python wrapper on Darknet
https://pypi.org/project/yolo34py/

sudo apt-get install python3-dev
sudo apt install pkg-config
pip3 install numpy
pip3 install cython
pip3 install opencv-python
pip3 install yolo34py     # CPU only
pip3 install yolo34py-gpu # GPU Accelerated
"""


ABS_PATH_TO_DARKNET = '/home/prince/Desktop/NESL/' # absolute path to darknet folder
tiny = False

def runYOLO(image_path):
  cfg = 'yolov3.cfg'
  weight = 'yolov3.weights'
  
  if tiny:
    cfg = 'yolov3-tiny.cfg'
    weight = 'yolov3-tiny.weights'

  try:
    os.mkdir('data')
    copy2('{}/darknet/data/coco.names'.format(ABS_PATH_TO_DARKNET), 'data')
  except: 
    pass
    
  detector = Detector(bytes('{0}/darknet/cfg/{1}'.format(ABS_PATH_TO_DARKNET, cfg), encoding="utf-8"),
                    bytes('{0}/darknet/{1}'.format(ABS_PATH_TO_DARKNET, weight), encoding="utf-8"), 0,
                    bytes('{0}/darknet/cfg/coco.data'.format(ABS_PATH_TO_DARKNET), encoding="utf-8"))
  rmtree('data')
  image = cv2.imread(image_path)
  results = detector.detect(Image(image))

  # Draw bounding boxes
  COLORS = np.random.randint(0, 255, size=(len(results), 3))
  count = 0
  for cat, score, bounds in results:
    color = tuple(map(int, COLORS[count]))
    x, y, w, h = bounds
    cv2.rectangle(image, (int(x - w / 2), int(y - h / 2)), (int(x + w / 2), int(y + h / 2)), color, thickness=2)
    cv2.putText(image, str(cat.decode("utf-8")), (int(x - w / 2)-10,int(y - h / 2)-10), cv2.FONT_HERSHEY_COMPLEX, 1, color, 2)  #BGR
    count = count + 1
    
  cv2.imwrite(image_path[:-4] + "-YOLO'd.jpg", image)



if __name__ == '__main__':
  if len(sys.argv) == 2 or len(sys.argv) == 3:
    if len(sys.argv) == 3 and sys.argv[2] == 'tiny':
      tiny = True
    runYOLO(sys.argv[1])

  else:
    print("Usage: python3 rasp_runYOLOPhoto.py <image path> {'tiny'}")
    exit(1)
