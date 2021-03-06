from time import sleep
import cv2
from cv2 import waitKey
from cv2 import destroyAllWindows
import numpy as np
import os


def face_boxes(image_filepath):
    # modelFile = "cs143-final-facebox-anime-stylize/face_test/res10_300x300_ssd_iter_140000.caffemodel"
    # configFile = "cs143-final-facebox-anime-stylize/face_test\deploy.prototxt"
    modelFile = "face_test/res10_300x300_ssd_iter_140000.caffemodel"
    configFile = "face_test/deploy.prototxt"
    net = cv2.dnn.readNetFromCaffe(configFile, modelFile)  # readNetFromCaffe

    im = cv2.imread(image_filepath)
    # directory = r'C:/Users/lizak\Desktop\Brown\Spring 2022/CSCI 1430/cs143-final-facebox-anime-stylize/face_test/results'
    # os.chdir(directory)
    h, w = im.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(im, (300, 300)), 1.0,
                                 (300, 300), (104.0, 117.0, 123.0))
    # ALT, from opencv: To achieve the best accuracy run the model on BGR images resized to
    # 300x300 applying mean subtraction of values (104, 177, 123) for each blue, green and red channels correspondingly.
    net.setInput(blob)
    faces = net.forward()
    face_boxes = []
    # print(faces)
    # to draw faces on image
    for i in range(faces.shape[2]):
        confidence = faces[0, 0, i, 2]
        if confidence > 0.5:
            box = faces[0, 0, i, 3:7] * np.array([w, h, w, h])
            box = box.astype("int")
            (x, y, x1, y1) = box
            im = cv2.rectangle(im, (x, y), (x1, y1), (0, 0, 255), 2)
            face_boxes.append(box)

    print(face_boxes)

    filename = 'facebox_dnn.jpg'
    cv2.imwrite(filename, im)

    cv2.imshow('face_test_boxes', im)
    # keep the window open until we press a key
    waitKey(0)
    # close the window
    destroyAllWindows()
    return face_boxes


def bb_style_face(style_image, target_image, bounds):
    # for i in range(bounds[0], bounds[1]):
    #     for j in range(bounds[2], bounds[3]):
    box_cut = target_image[bounds[0]:bounds[1], bounds[2]:bounds[3]]
    styled_box = stylify(style_image, box_cut)
    new_image = target_image
    new_image[bounds[0]:bounds[1], bounds[2]:bounds[3]] = styled_box
    return new_image

# def bb_style_face(style_image, target_image, bounds):
#     new_image = target_image
#     new_image[bounds[0]:bounds[1], bounds[2]:bounds[3]] =\
#         target_image[bounds[0]:bounds[1], bounds[2]:bounds[3]]
#     styled_target = stylify(style_image, new_image)
#     return styled_target

# modelFile = "cs143-final-facebox-anime-stylize/face_test/res10_300x300_ssd_iter_140000.caffemodel"
# configFile = "cs143-final-facebox-anime-stylize/face_test\deploy.prototxt"
# net = cv2.dnn.readNetFromCaffe(configFile, modelFile)  # readNetFromCaffe
# im = cv2.imread('cs143-final-facebox-anime-stylize/face_test/aot.jpg')
# directory = r'cs143-final-facebox-anime-stylize/face_test/results'
# os.chdir(directory)
# h, w = im.shape[:2]
# blob = cv2.dnn.blobFromImage(cv2.resize(im, (300, 300)), 1.0,
#                              (300, 300), (104.0, 117.0, 123.0))
# # ALT: To achieve the best accuracy run the model on BGR images resized to
# # 300x300 applying mean subtraction of values (104, 177, 123) for each blue, green and red channels correspondingly.
# net.setInput(blob)
# faces = net.forward()
# # print(faces)
# # to draw faces on image
# for i in range(faces.shape[2]):
#     confidence = faces[0, 0, i, 2]
#     if confidence > 0.5:
#         box = faces[0, 0, i, 3:7] * np.array([w, h, w, h])
#         (x, y, x1, y1) = box.astype("int")
#         im = cv2.rectangle(im, (x, y), (x1, y1), (0, 0, 255), 2)

# filename = 'facebox_dnn_aot.jpg'
# cv2.imwrite(filename, im)

# cv2.imshow('face_test_boxes', im)
# # keep the window open until we press a key
# waitKey(0)
# # close the window
# destroyAllWindows()
