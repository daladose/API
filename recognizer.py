import cv2
import numpy as np
from os import listdir, path
import os
import sys, time
import pickle

app_path = path.dirname(os.path.abspath(__file__))

class Recognizer:
    def __init__(self, app):
        self.storage = app.config['storage']
        self.eigen_model = cv2.face.EigenFaceRecognizer_create()

    # eigen_model = cv2.face.EigenFaceRecognizer_create()
    # app_path = path.dirname(os.path.abspath(__file__))

    def get_images(self, path, size):
        sub = 0
        images, labels = [], []
        people = []

        for subdir in listdir(path):
            for image in listdir(path + "/" + subdir):
                img = cv2.imread(path + "/" + subdir + "/" + image, cv2.IMREAD_GRAYSCALE)
                img = cv2.resize(img, size)

                images.append(np.asarray(img, dtype=np.uint8))
                labels.append(sub)

            people.append(subdir)
            sub += 1

        return [images, labels, people]


    # training model
    def recognize_face(self, sorted, testing):

        [images, labels, people] = self.get_images(sorted, (256, 256))  #path, size

        labels = np.asarray(labels, dtype=np.int32)

        print("Initializing eigen FaceRecognizer and training...")
        sttime = time.clock()
        # eigen_model = cv2.face.EigenFaceRecognizer_create()

        # saving model
        model_obj = self.eigen_model.train(images, labels)
        with open('saved_model/eigen_model.pkl','wb') as f:
            pickle.dump(model_obj,f)
        print("\tCompleted training in " + str(time.clock() - sttime) + " Secs!")

        response_message = "Completed registration in " + str(time.clock() - sttime) + " Secs!"
        return response_message

    # testing model
    def predictor_face(self, filename):
        full_path_file = self.storage+"/unknown/"+filename
        # print("Filename is : ",filename)
        # print("Full Path is : ",full_path_file)

        [images, labels, people] = self.get_images(self.storage+"/croped_images", (256, 256))

        try:
            color_image = cv2.imread(full_path_file)
            [x, y] = color_image.shape[:2]
            x_factor = (float(y) / x)
            resize_y = 480

            color_image = cv2.resize(color_image, (int(resize_y * x_factor), resize_y))

            pre_image = cv2.imread(full_path_file, cv2.IMREAD_GRAYSCALE)
            pre_image = cv2.resize(pre_image, (int(resize_y * x_factor), resize_y))
        except:
            print("Couldn't read image. Please check the path to image file.")
            sys.exit()

        frontal_face = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

        # bBoxes= frontal_face.detectMultiScale(pre_image,
        # 	scaleFactor=1.3, minNeighbors=4, minSize=(30, 30),
        # 	flags = cv.CV_HAAR_SCALE_IMAGE)
        bBoxes = frontal_face.detectMultiScale(
            pre_image,
            scaleFactor=1.3,
            minNeighbors=4,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        with open(app_path + '/saved_model/eigen_model.pkl','rb') as f:
            model_obj = pickle.load(f)
        for bBox in bBoxes:
            (p, q, r, s) = bBox

            cv2.rectangle(color_image, (p, q), (p + r, q + s), (2, 255, 25), 2)

            pre_crop_image = pre_image[q:q + s, p:p + r]
            pre_crop_image = cv2.resize(pre_crop_image, (256, 256))

            [predicted_label, predicted_conf] = self.eigen_model.predict(np.asarray(pre_crop_image))
            print("Predicted person in the image " + full_path_file + " : " + people[predicted_label])
            subject_name = people[predicted_label]
            print(subject_name)
        return subject_name
        
