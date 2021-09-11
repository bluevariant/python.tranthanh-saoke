import pytesseract
import json
import cv2
from utils import readdir
import numpy as np
from PIL import Image


def rectangle(image, item, color=(0, 255, 0), padding=5):
    return cv2.rectangle(
        image,
        (item["left"] - padding, item["top"] - padding),
        (
            item["left"] + item["width"] + padding,
            item["top"] + item["height"] + padding,
        ),
        color,
        1,
    )


def clarify_tesseract_result(result):
    text_info = []

    for i in range(0, len(result["text"])):
        if float(result["conf"][i]) > 0 and len(result["text"][i].strip()) > 0:
            text_info.append(
                {
                    "text": result["text"][i],
                    "conf": float(result["conf"][i]),
                    "left": int(result["left"][i]),
                    "top": int(result["top"][i]),
                    "width": int(result["width"][i]),
                    "height": int(result["height"][i]),
                }
            )

    return text_info


def tesseract_orc(image):
    image = preprocessing(image)


def preprocessing(image):
    # image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 15)

    # kernel = np.ones((2, 2), np.uint8)
    # image = cv2.dilate(image, kernel, iterations=1)

    # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # kernel = np.ones((2, 2), np.uint8)
    # image = cv2.erode(image, kernel, iterations=1)

    # kernel = np.ones((2, 2), np.uint8)
    # image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

    # image = cv2.Canny(image, 100, 200)

    # image = cv2.medianBlur(image, 1)

    # cv2.imshow("", image)
    # cv2.waitKey()

    return image


def tesseract_processor(filename, debug=False):
    filename_processed = filename + ".tesseract.jpg"
    image = preprocessing(cv2.imread(filename=filename))
    result_texts = pytesseract.image_to_data(
        image=image,
        output_type=pytesseract.Output.DICT,
    )
    result_numbers = pytesseract.image_to_data(
        image=image,
        output_type=pytesseract.Output.DICT,
        config="-c tessedit_char_whitelist=0123456789.,;",
    )
    info_texts = clarify_tesseract_result(result_texts)
    info_numbers = clarify_tesseract_result(result_numbers)
    debit_text = None
    balance_text = None

    for i in range(0, len(info_texts)):
        text = info_texts[i]

        if text["text"] == "Debit" and (
            debit_text is None or debit_text["top"] < text["top"]
        ):
            debit_text = text
            image = rectangle(image=image, item=text)

        if text["text"] == "Balance" and (
            balance_text is None or balance_text["top"] < text["top"]
        ):
            balance_text = text
            image = rectangle(image=image, item=text)

    if debit_text is None or balance_text is None:
        raise Exception("can't find the area at: {}".format(filename))

    area = {
        "left": debit_text["left"] + debit_text["width"],
        "right": balance_text["left"],
        "top": int(
            (
                (debit_text["top"] + debit_text["height"])
                + (balance_text["top"] + balance_text["height"])
            )
            / 2
        ),
        "width": balance_text["left"] - (debit_text["left"] + debit_text["width"]),
        "height": 696969,  # image height
    }

    image = rectangle(image=image, item=area, padding=0)

    for i in range(0, len(info_numbers)):
        text = info_numbers[i]

        if (
            text["left"] > area["left"]
            and (text["left"] + text["width"]) < area["right"]
            and text["top"] > area["top"]
        ):
            image = rectangle(image=image, item=text)
            print(text)

    cv2.imwrite(filename_processed, image)

    if debug:
        cv2.imshow("drawed", image)
        cv2.waitKey()


if __name__ == "__main__":
    images_path = "C:\\Users\\dccxx\\Downloads\\21-20210910T111338Z-001"
    jpg_files = readdir(root_dir=images_path, pattern="**/*.jpg")

    for i in range(0, len(jpg_files)):
        filename = jpg_files[i]

        if filename.endswith("tesseract.jpg") or filename.endswith("google.jpg"):
            continue

        tesseract_processor(jpg_files[i], debug=False)
        print(jpg_files[i])
