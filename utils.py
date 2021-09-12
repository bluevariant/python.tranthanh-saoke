import glob
import base64
import json
import cv2

from typing import List
from os import path


def readdir(root_dir: str, pattern: str) -> List[str]:
    files: List[str] = []

    for filename in glob.iglob(path.join(root_dir, pattern), recursive=True):
        files.append(filename)

    return files


def image_to_base64(image):
    return base64.b64encode(cv2.imencode(".jpg", image)[1]).decode()
