import glob

from typing import List
from os import path


def readdir(root_dir: str, pattern: str) -> List[str]:
    files: List[str] = []

    for filename in glob.iglob(path.join(root_dir, pattern), recursive=True):
        files.append(filename)

    return files
