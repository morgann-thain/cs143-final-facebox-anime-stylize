import time
import PIL.Image
import numpy as np
import os
import tensorflow as tf
from mtcnn.mtcnn import MTCNN

import matplotlib.pyplot as plt
import matplotlib as mpl
import cv2
from cv2 import waitKey
from cv2 import destroyAllWindows
mpl.rcParams['figure.figsize'] = (12, 12)
mpl.rcParams['axes.grid'] = False

np.random.seed(7)


def face_boxes_dnn(image_filepath):
    modelFile = "dnn_model/res10_300x300_ssd_iter_140000.caffemodel"
    configFile = "dnn_model/deploy.prototxt"
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


def face_boxes_mtcnn(image_filepath):
    detector = MTCNN()
    img = cv2.imread(image_filepath)
    faces = detector.detect_faces(img)  # result
    # directory = r'cs143-final-facebox-anime-stylize/face_test/results'
    # os.chdir(directory)
    # to draw faces on image

    face_boxes = []
    for result in faces:
        x, y, w, h = result['box']
        x1, y1 = x + w, y + h
        box = (x, y, x1, y1)
        cv2.rectangle(img, (x, y), (x1, y1), (0, 0, 255), 2)
        face_boxes.append(box)

    writepath = 'results/facebox_mtcnn.jpg'
    cv2.imwrite(writepath, img)

    cv2.imshow('face_test_boxes', img)
    # keep the window open until we press a key
    waitKey(0)
    # close the window
    destroyAllWindows()
    print(face_boxes)
    return face_boxes


def bb_style_face(style_image_path, target_image, bounds):
    style_image = load_img(style_image_path)
    box_cut = preprocess_img(
        target_image[bounds[1]:bounds[3], bounds[0]:bounds[2], :])
    styled_box = stylize(style_image, box_cut)
    # TODO: fix below line so that it doesn't show up as disgusting bg
    new_image = np.array(target_image)
    new_image[bounds[1]:bounds[3], bounds[0]:bounds[2], :] = tf.image.resize(
        styled_box, (abs(bounds[1]-bounds[3]), abs(bounds[0]-bounds[2])))
    return new_image


def tensor_to_image(tensor):
    tensor = tensor*255
    tensor = np.array(tensor, dtype=np.uint8)
    if np.ndim(tensor) > 3:
        assert tensor.shape[0] == 1
        tensor = tensor[0]
    return PIL.Image.fromarray(tensor)


def preprocess_img(img):
    img = np.copy(img)
    max_dim = 512
    # img = tf.image.decode_image(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)
    shape = tf.cast(tf.shape(img)[:-1], tf.float32)
    long_dim = max(shape)
    scale = max_dim / long_dim
    new_shape = tf.cast(shape * scale, tf.int32)

    img = tf.image.resize(img, new_shape)
    img = img[tf.newaxis, :]
    return img


def load_img(path_to_img):
    max_dim = 512
    img = tf.io.read_file(path_to_img)
    img = tf.image.decode_image(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)

    shape = tf.cast(tf.shape(img)[:-1], tf.float32)
    long_dim = max(shape)
    scale = max_dim / long_dim

    new_shape = tf.cast(shape * scale, tf.int32)

    img = tf.image.resize(img, new_shape)
    img = img[tf.newaxis, :]
    return img


def imshow(image, title=None):
    if len(image.shape) > 3:
        image = tf.squeeze(image, axis=0)

    plt.imshow(image)
    if title:
        plt.title(title)


def vgg_layers(layer_names):
    """ Creates a vgg model that returns a list of intermediate output values."""
    # Load our model. Load pretrained VGG, trained on imagenet data
    vgg = tf.keras.applications.VGG19(include_top=False, weights='imagenet')
    vgg.trainable = False

    outputs = [vgg.get_layer(name).output for name in layer_names]

    model = tf.keras.Model([vgg.input], outputs)
    return model


def gram_matrix(input_tensor):
    result = tf.linalg.einsum('bijc,bijd->bcd', input_tensor, input_tensor)
    input_shape = tf.shape(input_tensor)
    num_locations = tf.cast(input_shape[1]*input_shape[2], tf.float32)
    return result/(num_locations)


class StyleContentModel(tf.keras.models.Model):
    def __init__(self, style_layers, content_layers):
        super(StyleContentModel, self).__init__()
        self.vgg = vgg_layers(style_layers + content_layers)
        self.style_layers = style_layers
        self.content_layers = content_layers
        self.num_style_layers = len(style_layers)
        self.vgg.trainable = False

    def call(self, inputs):
        "Expects float input in [0,1]"
        inputs = inputs*255.0
        preprocessed_input = tf.keras.applications.vgg19.preprocess_input(
            inputs)
        outputs = self.vgg(preprocessed_input)
        style_outputs, content_outputs = (outputs[:self.num_style_layers],
                                          outputs[self.num_style_layers:])

        style_outputs = [gram_matrix(style_output)
                         for style_output in style_outputs]

        content_dict = {content_name: value
                        for content_name, value
                        in zip(self.content_layers, content_outputs)}

        style_dict = {style_name: value
                      for style_name, value
                      in zip(self.style_layers, style_outputs)}

        return {'content': content_dict, 'style': style_dict}


def clip_0_1(image):
    return tf.clip_by_value(image, clip_value_min=0.0, clip_value_max=1.0)


def stylize(style_image, content_image):
    plt.subplot(1, 2, 1)
    imshow(content_image, 'Content Image')

    plt.subplot(1, 2, 2)
    imshow(style_image, 'Style Image')
    plt.show()
    x = tf.keras.applications.vgg19.preprocess_input(content_image*255)
    x = tf.image.resize(x, (224, 224))
    vgg = tf.keras.applications.VGG19(include_top=False, weights='imagenet')

    content_layers = ['block5_conv2']

    style_layers = ['block1_conv1',
                    'block2_conv1',
                    'block3_conv1',
                    'block4_conv1',
                    'block5_conv1']

    num_content_layers = len(content_layers)
    num_style_layers = len(style_layers)

    style_extractor = vgg_layers(style_layers)
    style_outputs = style_extractor(style_image*255)

    extractor = StyleContentModel(style_layers, content_layers)

    results = extractor(tf.constant(content_image))

    style_targets = extractor(style_image)['style']
    content_targets = extractor(content_image)['content']

    image = tf.Variable(content_image)

    opt = tf.optimizers.Adam(learning_rate=0.02, beta_1=0.99, epsilon=1e-1)

    style_weight = 1e-3
    content_weight = 1e3

    def style_content_loss(outputs):
        style_outputs = outputs['style']
        content_outputs = outputs['content']
        style_loss = tf.add_n([tf.reduce_mean((style_outputs[name]-style_targets[name])**2)
                               for name in style_outputs.keys()])
        style_loss *= style_weight / num_style_layers

        content_loss = tf.add_n([tf.reduce_mean((content_outputs[name]-content_targets[name])**2)
                                for name in content_outputs.keys()])
        content_loss *= content_weight / num_content_layers
        loss = style_loss + content_loss
        return loss

    total_variation_weight = 25

    def total_variation_loss(image):
        x_deltas, y_deltas = high_pass_x_y(image)
        return tf.reduce_sum(tf.abs(x_deltas)) + tf.reduce_sum(tf.abs(y_deltas))

    @tf.function()
    def train_step(image):
        with tf.GradientTape() as tape:
            outputs = extractor(image)
            loss = style_content_loss(outputs)
            loss += total_variation_weight * total_variation_loss(image)

        grad = tape.gradient(loss, image)
        opt.apply_gradients([(grad, image)])
        image.assign(clip_0_1(image))

    start = time.time()

    epochs = 5
    steps_per_epoch = 100

    step = 0
    for n in range(epochs):
        for m in range(steps_per_epoch):
            step += 1
            train_step(image)
            print(".", end='', flush=True)
        print("Train step: {}".format(step))

    end = time.time()
    print("Total time: {:.1f}".format(end-start))
    return image


def high_pass_x_y(image):
    x_var = image[:, :, 1:, :] - image[:, :, :-1, :]
    y_var = image[:, 1:, :, :] - image[:, :-1, :, :]

    return x_var, y_var


if __name__ == "__main__":
    style_path = 'images/mikasa.png'
    content_path = "images/shangchi.png"

    content_image = tf.io.read_file(content_path)
    content_image = tf.image.decode_image(content_image, channels=3)
    content_image = tf.image.convert_image_dtype(content_image, tf.float32)
    bounds = face_boxes_mtcnn(content_path)
    for bound in bounds:
        content_image = bb_style_face(style_path, content_image, bound)

    # directory = r'cs143-final-facebox-anime-stylize\style_transfer/results'
    # os.chdir(directory)
    # filename = 'New Content Image.jpg'
    # cv2.imwrite(filename, tensor_to_image(content_image))

    final = tensor_to_image(content_image)
    plt.imshow(final)
    plt.show()

    filename = 'results\Final_Image.jpg'
    final.save(filename)
