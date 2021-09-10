from typing import List
from utils import readdir
from wand.image import Image
import os


def processor_image(filename: str):
    output: str = filename + ".jpg"

    with Image(filename=heic_files[0]) as image:
        image.format = "jpg"

        image.resize(int(image.width / 2), int(image.height / 2))
        image.save(filename=output)


if __name__ == "__main__":
    # Download and unzip: https://drive.google.com/drive/folders/18-FsuqHkyE38udx5gIMTb5hEZhcxVyc4?fbclid=IwAR1TIegRQ1lke7NiR_K9N-TRWCD5C_fImxW-71_EFrw6tjJbcQMWpeTJoLw
    images_path: str = "C:\\Users\\dccxx\\Downloads\\21-20210910T111338Z-001\\SAO KÊ TỪ THIỆN MIỀN TRUNG 15-10-20 - 06-09-21"
    heic_files: List[str] = readdir(root_dir=images_path, pattern="**/*.HEIC")

    for i in range(0, len(heic_files)):
        if not os.path.isfile(heic_files[i] + ".jpg"):
            processor_image(heic_files[i])

        print("{}: {}".format(i + 1, heic_files[i]))

    for i in range(0, len(heic_files)):
        if os.path.isfile(heic_files[i] + ".jpg"):
            os.unlink(heic_files[i])

    print("total {} files.".format(len(heic_files)))
