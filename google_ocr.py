import cv2
import requests
import json
import os
import time
import numpy as np
import re

from utils import image_to_base64, readdir

API_KEY = ""


def call_api(image, filename=None, retries=0, max_retries=3, retry_delay=1):
    if filename is not None:
        cache_request_response = filename + ".json"

        if os.path.isfile(cache_request_response):
            with open(cache_request_response) as f:
                return json.load(f)

    endpoint = "https://content-vision.googleapis.com/v1/images:annotate?alt=json&key={}".format(
        API_KEY
    )
    response = requests.post(
        endpoint,
        headers={"x-referer": "https://explorer.apis.google.com"},
        json={
            "requests": [
                {
                    "image": {"content": image_to_base64(image)},
                    "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                },
            ]
        },
    ).json()

    if "responses" in response and len(response["responses"]) > 0:
        if filename is not None:
            with open(cache_request_response, "w") as f:
                f.write(json.dumps(response))
                f.close()

        return response

    if retries < max_retries:
        time.sleep(retry_delay)

        return call_api(image, filename, retries + 1, max_retries)
    else:
        raise Exception("something went wrong: {}".format(filename))


def box(image, text, color=(0, 255, 0)):
    pts = np.array(
        [text["tl"], text["tr"], text["br"], text["bl"]],
        np.int32,
    ).reshape((-1, 1, 2))

    cv2.polylines(image, [pts], True, color, 1)


def processor(filename, total):
    image = cv2.imread(filename)
    response = call_api(image, filename)
    texts = []

    for i in range(0, len(response["responses"])):
        for j in range(0, len(response["responses"][i]["textAnnotations"])):
            text = response["responses"][i]["textAnnotations"][j]
            position = text["boundingPoly"]["vertices"]

            if "locale" in text:
                continue

            clarify_text = {
                "filename": filename,
                "text": text["description"],
                "tl": (
                    position[0]["x"] if "x" in position[0] else 0,
                    position[0]["y"] if "y" in position[0] else 0,
                ),
                "tr": (
                    position[3]["x"] if "x" in position[3] else 0,
                    position[3]["y"] if "y" in position[3] else 0,
                ),
                "bl": (
                    position[1]["x"] if "x" in position[1] else 0,
                    position[1]["y"] if "y" in position[1] else 0,
                ),
                "br": (
                    position[2]["x"] if "x" in position[2] else 0,
                    position[2]["y"] if "y" in position[2] else 0,
                ),
                "top": min(
                    position[0]["y"] if "y" in position[0] else 0,
                    position[3]["y"] if "y" in position[3] else 0,
                ),
                "left": min(
                    position[0]["x"] if "x" in position[0] else 0,
                    position[1]["x"] if "x" in position[1] else 0,
                ),
                "bottom": max(
                    position[1]["y"] if "y" in position[1] else 0,
                    position[2]["y"] if "y" in position[2] else 0,
                ),
                "right": max(
                    position[2]["x"] if "x" in position[2] else 0,
                    position[3]["x"] if "x" in position[3] else 0,
                ),
            }

            texts.append(clarify_text)

    credit_text = None
    tnx_text = None

    for i in range(0, len(texts)):
        text = texts[i]

        if text["text"] == "Credit":
            credit_text = text

        if text["text"] == "TNX":
            tnx_text = text

    # if balance_text is None or debit_text is None:
    if credit_text is None or tnx_text is None:
        # raise Exception("something went wrong: {}".format(filename))
        print(filename)

    width = (credit_text["right"] - credit_text["left"]) * 3

    area = {
        "top": credit_text["bottom"],
        "left": credit_text["left"] - width,
        "right": credit_text["right"] + width,
    }

    dates = []
    currencies = []

    for i in range(0, len(texts)):
        text = texts[i]

        if text["top"] > area["top"] and re.match(
            "[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}", text["text"]
        ):
            dates.append(text)
            box(image, text)

        if (
            text["left"] > area["left"]
            and text["top"] > area["top"]
            and text["right"] < area["right"]
        ):
            # https://regex101.com/r/1lxTKJ/1/
            if re.match(
                "^[+-]?[0-9]{1,3}(?:[0-9]*(?:[.,][0-9]{2})?|(?:,[0-9]{3})*(?:\.[0-9]{2})?|(?:\.[0-9]{3})*?)$",
                text["text"],
            ):
                box(image, text)

                money = text["text"].replace(".", "").replace(",", "")

                if len(money) <= 3:
                    print("warn (01): {}: {}".format(filename, text["text"]))
                    box(image, text, (0, 0, 255))

                currencies.append(text)
            else:
                print("warn (02): {}: {}".format(filename, text["text"]))
                box(image, text, (0, 0, 255))

    for i in range(0, min(len(dates), len(currencies))):
        currency = currencies[i]
        date = dates[i]
        money = int(currency["text"].replace(".", "").replace(",", ""))
        pts = np.array(
            [currency["tr"], date["br"]],
            np.int32,
        ).reshape((-1, 1, 2))

        total += money

        cv2.polylines(image, [pts], False, (0, 255, 0), 1)
        cv2.putText(
            image,
            "{:,.2f}".format(total).split(".")[0].replace(",", "."),
            (
                currency["right"] + int(currency["bottom"] - currency["top"]),
                currency["bottom"],
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            image,
            "+{:,.2f}".format(money).split(".")[0].replace(",", "."),
            (
                currency["left"]
                - int(currency["bottom"] - currency["top"])
                - (currency["right"] - currency["left"]),
                currency["bottom"],
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )

    if len(dates) != len(currencies):
        print("warn (03): {}".format(filename))

    # QUANG CAO hộ đứa bạn đang chạy KPI =))
    ads = [
        "DU LIEU DO THUAT TOAN TU SINH, CO SAI SOT, CHI MANG TINH THAM KHAO",
        # "FB thang em IT 96: dev.nvdong",
        # "Sieu uu dai tai khoan ngan hang so SIEU DEP: https://bit.ly/banksodep",
    ]
    offset = 30

    for i in range(0, len(ads)):
        cv2.putText(
            image,
            ads[i],
            (60, (i + 1) * 36 + offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
    #

    output = filename + ".processed.jpg"
    cv2.imwrite(output, image)

    return total


if __name__ == "__main__":
    images_path = "C:\\Users\\dccxx\\Downloads\\21-20210910T111338Z-001"
    jpg_files = readdir(root_dir=images_path, pattern="**/*.processed.jpg")

    for i in range(0, len(jpg_files)):
        filename = jpg_files[i]

        if filename.endswith(".processed.jpg"):
            os.unlink(filename)

    jpg_files = readdir(root_dir=images_path, pattern="**/*.jpg")
    n = len(jpg_files)

    for i in range(n - 1):
        for j in range(0, n - i - 1):
            filename = jpg_files[j].replace("\\", "/").split("/").pop()
            filename2 = jpg_files[j + 1].replace("\\", "/").split("/").pop()

            if filename > filename2:
                jpg_files[j], jpg_files[j + 1] = jpg_files[j + 1], jpg_files[j]

    total = 0

    for i in range(0, len(jpg_files)):
        filename = jpg_files[i]

        if filename.endswith(".processed.jpg") or os.path.isfile(
            filename + ".processed.jpg"
        ):
            continue

        # print(filename)
        total = processor(filename, total=total)
