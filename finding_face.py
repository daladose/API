
import cv2
from os import listdir, path
import os
import time


app_path = path.dirname(os.path.abspath(__file__))

def call_test(arg):
    return arg

def cropImage(img, box, name, username):
	[p, q, r, s]= box

	write_img_color= img[q:q+ s, p:p+ r]
	saveCropped(write_img_color, name, username)


def saveCropped(img, name, username):
    print(username)
    after_crop_image_dir = path.join(app_path,'storage/croped_images/'+username+"/")
    cv2.imwrite(after_crop_image_dir +name+ ".jpg", img)


def crop_face_process(username, input_path):
	# input_dir = input_path
    # print(input_path)
	frontal_face = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
	input_names = listdir(input_path)
	print(input_names)
	print("Starting to detect faces and save the cropped images to output file...")
	sttime= time.clock()
	# image = cv2.imread(input_path,1)
	# cv2.imshow("image", image)
	# cv2.waitKey(3600)
	i= 1
	for name in input_names:
		print(input_path+name)
		color_img= cv2.imread(input_path+"/"+name)
		gray_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)

		bBoxes= frontal_face.detectMultiScale(gray_img, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30), flags = cv2.CASCADE_SCALE_IMAGE)
		print(bBoxes)

		for box in bBoxes:

			cropImage(color_img, box, name, username)
			i+= 1
	print("Completed the task in %.2f Secs." % (time.clock()- sttime))
