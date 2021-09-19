from utils import readdir
import cv2
import errno
import os
import shutil


def copy_to(src, dest):
    try:
        shutil.copy(src, dest)
    except IOError as e:
        # ENOENT(2): file does not exist, raised also on missing dest parent dir
        if e.errno != errno.ENOENT:
            raise
        # try creating parent directories
        os.makedirs(os.path.dirname(dest))
        shutil.copy(src, dest)


if __name__ == "__main__":
    images_path = "C:\\Users\\dccxx\\Downloads\\21-20210910T111338Z-001"
    jpg_files = readdir(root_dir=images_path, pattern="**/*.processed.jpg")

    for i in range(0, len(jpg_files)):
        copy_to(
            jpg_files[i],
            jpg_files[i].replace("\\images\\", "\\processed-images\\"),
        )
