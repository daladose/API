import cv2
from os import listdir, path
import os
import time

image = cv2.imread('/Users/sprite/Desktop/API/face-recognition-service/storage/pre_croped_images/daladose/phuwadet_01.jpg')
cv2.imshow("image", image)
cv2.waitKey(3600)
