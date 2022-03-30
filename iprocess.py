import socket
import select
import errno
import sys
import cv2 as cv
import numpy as np
import requests
import time

# global message
HEADER_LENGTH = 10

IP = "192.168.43.52"
PORT = 5050
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ __
my_username = "head"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect((IP, PORT))
client_socket.setblocking(False)

username = my_username.encode("utf-8")
username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
client_socket.send(username_header + username)

#################################################################################################################
# ip webcam live streaming link
url = 'http://192.168.43.1:8080/shot.jpg'
image_browser = requests.get(url)
img_arr = np.array(bytearray(image_browser.content), dtype=np.uint8)
img1 = cv.imdecode(img_arr, -1)
frame1 = cv.resize(img1, (int(img1.shape[1] * 0.55), int(img1.shape[0] * 0.55)), interpolation=cv.INTER_AREA)
image_browser = requests.get(url)
img_arr = np.array(bytearray(image_browser.content), dtype=np.uint8)
img2 = cv.imdecode(img_arr, -1)
frame2 = cv.resize(img2, (int(img2.shape[1] * 0.55), int(img2.shape[0] * 0.55)), interpolation=cv.INTER_AREA)
size_video = ((img2.shape[1], img2.shape[0]))

##############################################################################################################
# counter section
c_start_r1 = 0
c_right_r1 = 0
c_left_r1 = 0
c_end_r1 = 0

##############################################################################################################
counter = 0
while True:

    diff = cv.absdiff(frame1, frame2)
    gray = cv.cvtColor(diff, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray, (7, 7), 1)
    _, thres = cv.threshold(blur, 20, 255, cv.THRESH_BINARY)
    dilated = cv.dilate(thres, None, iterations=3)
    cv.line(frame1, (0, 490), (frame1.shape[1], 490), (0, 225, 0), 2)  # right line(0,490),(1056,490)
    cv.line(frame1, (0, 450), (frame1.shape[1], 450), (0, 0, 225), 2)

    cv.line(frame1, (0, 70), (frame1.shape[1], 70), (0, 0, 225), 2)  # start line y=70
    cv.line(frame1, (0, 100), (frame1.shape[1], 100), (0, 225, 0), 2)  # y=100
    cv.line(frame1, (290, 0), (50, frame1.shape[0]), (0, 225, 0), 2)  # end line(290,0),(50,594)
    cv.line(frame1, (340, 0), (100, frame1.shape[0]), (0, 0, 225), 2)
    cv.line(frame1, (290 + 200, 0), (50 + 400, frame1.shape[0]), (0, 225, 0), 2)  # left line(490,0),(450,594)
    cv.line(frame1, (290 + 200 - 50, 0), (50 + 400 - 50, frame1.shape[0]), (0, 0, 225), 2)

    # print(((290,0),(50,frame1.shape[0])))
    # print(((290+200,0),(50+400,frame1.shape[0])))

    contours, _ = cv.findContours(dilated, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        (x, y, w, h) = cv.boundingRect(contour)

        if cv.contourArea(contour) < 1900:
            continue
        print((x, y))
        # print(cv.contourArea(contour))
        cv.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
        ####################################################################################################################

        # if robot reaches right line
        if (y <= 490 and y > 450 and c_right_r1 == 0):
            message = "R1 RIGHT"
            message_header = f"{len(message) :< {HEADER_LENGTH}}"
            final_message = (message_header + message).encode("utf-8")
            client_socket.send(final_message)
            c_right_r1 += 1

        # if robot reaches endline---------->99x +40y=28710
        if (99 * x + 40 * y <= 28710 and 99 * x + 40 * y >= 3360 and c_end_r1 == 0 and c_right_r1 == 1):
            message = "R1 UNLOAD"
            message_header = f"{len(message) :< {HEADER_LENGTH}}"
            final_message = (message_header + message).encode("utf-8")
            client_socket.send(final_message)
            c_end_r1 += 1

        # if robot reaches left line--------> 297 x + 20 y = 145530
        if (c_end_r1 == 1 and 297 * x + 20 * y >= 145530 and 297 * x + 20 * y <= 160380):
            message = "R1 LEFTb"
            message_header = f"{len(message) :< {HEADER_LENGTH}}"
            final_message = (message_header + message).encode("utf-8")
            client_socket.send(final_message)
            c_end_r1 += 1

        #         #if robot reaches back starting point
        if (c_end_r1 == 2 and y >= 70 and y <= 100):
            message = "R1 STOP"
            message_header = f"{len(message) :< {HEADER_LENGTH}}"
            final_message = (message_header + message).encode("utf-8")
            client_socket.send(final_message)
            c_end_r1 += 1
            c_start_r1 += 1

    # ####################################################################################################################
    cv.imshow('Live Stream', frame1)
    # start of the journey!!!
    if counter == 0:
        message = "R1 FORWARD"
        message_header = f"{len(message) :< {HEADER_LENGTH}}"
        final_message = (message_header + message).encode("utf-8")
        client_socket.send(final_message)
        counter += 1

    frame1 = frame2

    image_browser = requests.get(url)
    img_arr = np.array(bytearray(image_browser.content), dtype=np.uint8)
    img = cv.imdecode(img_arr, -1)
    frame2 = cv.resize(img, (int(img.shape[1] * 0.55), int(img.shape[0] * 0.55)), interpolation=cv.INTER_AREA)

    if cv.waitKey(40) & 0xFF == ord('d'):
        break