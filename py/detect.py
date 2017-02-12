#!/usr/bin/env python
"""
Quick and dirty darknet detections from python via stdin & stdout.

This requires a slight tweak to the darknet detections output to include the bounding box.
"""

import subprocess
from collections import namedtuple

from os import O_NONBLOCK, read,  write
from fcntl import fcntl, F_GETFL, F_SETFL

# define some named tuples for the detectiona and bounding  box
Detection = namedtuple("Detection", ['name', 'confidence', 'box'])

Box = namedtuple('Box', ['left', 'right', 'top', 'bottom'])


# open darknet process in detection mode
# This uses the added 'detect_nodraw' mode to skip the output image and instead output bounding box coordinates.
dark_args = ['./darknet', 'detect_nodraw',  'cfg/yolo.cfg', 'yolo.weights']
proc = subprocess.Popen(dark_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

# put stdout into nonblocking mode
flags = fcntl(proc.stdout, F_GETFL)
fcntl(proc.stdout, F_SETFL, flags | O_NONBLOCK)

# wait for the prompt to appear
buf = ""
while True:
    try:
        outp = read(proc.stdout.fileno(), 8192)
    except:
        continue
    buf += outp
    match = 'Enter Image Path: '
    if buf.endswith(match):
        break


def parse_prediction(ptxt):
    """
    parse one prediction line of the (cogniac modified) output of the darknet detector

    returns Detection namedtuple, which includes a class name, confidence and Box namedtuple
    The box includes the integer pixel offselfs of the left, right, top and bottom of the detection.
    """
    sub, pred = ptxt.split(":")
    pred = pred.split(' ')
    conf = pred[1][:-1]
    conf = float(conf)/100
    box = pred[-4:]
    box = [int(x) for x in box]
    left, right, top, bot = box
    return Detection(sub, conf, Box(left, right, top, bot))


def darknet_detections(filename):
    """
    send the specified image filename to darknet for detections.
    return a list of Detections named tuples.
    Each Detection tuple includes a class name, confidence and Box
    The box includes the integer pixel offselfs of the left, right, top and bottom of the detection.
    """
    write(proc.stdin.fileno(), filename+"\n")

    buf = ""
    while True:
        try:
            outp = read(proc.stdout.fileno(), 8192)
        except KeyboardInterrupt:
            raise
        except:
            continue
        buf += outp
        print buf
        match = 'Enter Image Path: '
        if buf.endswith(match):
            break
    predictions = buf.split('\n')[1:-1]
    predictions = [parse_prediction(p) for p in predictions]
    return predictions


if __name__ == "__main__":
    print darknet_detections('data/dog.jpg')
    print darknet_detections('data/eagle.jpg')
