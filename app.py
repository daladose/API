from flask import Flask, json, Response, request, render_template
from werkzeug.utils import secure_filename
import base64
from os import path, getcwd
import os
import time
from db import Database
from face import Face
from finding_face import *
from recognizer import Recognizer


app = Flask(__name__)

app.config['file_allowed'] = ['image/png', 'image/jpeg']
app.config['storage'] = path.join(getcwd(), 'storage')
app.config['after_crop_image'] = path.join(getcwd(), 'storage/croped_images')
app.config['app_path'] = path.dirname(os.path.abspath(__file__))
app_path = path.dirname(os.path.abspath(__file__))
app.db = Database()
app.face = Face(app)
app.recognizer = Recognizer(app)


def create_directory_before_crop_images(username):
    user_directory = path.join(app.config['storage'], 'pre_croped_images')
    try:
        os.mkdir(user_directory+"/"+username)
    except FileExistsError:
        print("You already have directory name ",username)


def create_directory_after_crop_images(username):
    output_directory = path.join(app.config['storage'], 'croped_images')
    try:
        os.mkdir(output_directory+"/"+username)

    except FileExistsError:
        print("You already have directory name ",username)


def upload_to_before_crop_images(username):
    target = os.path.join ( app_path, "storage/pre_croped_images/"+username)
    print ( target )

    if not os.path.isdir ( target ):
        os.mkdir ( target )

    for file in request.files.getlist ( "file" ):
        print ( file )
        filename = file.filename
        destination = "/".join ( [target, filename] )
        print ( destination )
        file.save ( destination )

    return "Upload Success"


def train_model():
    registration_status = app.recognizer.recognize_face("./storage/croped_images", "./storage/unknown")
    registration_status_message = {"registration_status": registration_status}
    return success_handle(json.dumps(registration_status_message))


def decode_base64(imgstring, image_file_name):
    imgdata = base64.b64decode(imgstring)
    filename = image_file_name+".jpg"
    with open(app.config['storage']+"/unknown/"+filename, 'wb') as f:
        f.write(imgdata)
    return filename


def encode_base64(path):
    with open(path, "rb") as image_file:
        base64_string = base64.b64encode(image_file.read())
    return base64_string


def success_handle(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)


def error_handle(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({"error": {"message": error_message}}), status=status, mimetype=mimetype)


def get_user_by_id(user_id):
    user = {}
    results = app.db.select(
        'SELECT users.id, users.username, users.firstname, users.lastname, users.email, users.tel, users.created, faces.id, faces.user_id, faces.filename, faces.created FROM users LEFT JOIN faces ON faces.user_id = users.id WHERE users.id = ?',
        [user_id])

    index = 0
    for row in results:
        print (row)
        face = {
            "id": row[7],
            "user_id": row[8],
            "filename": row[9],
            "created": row[10],
        }
        if index == 0:
            user = {
                "id": row[0],
                "username": row[1],
                "firstname": row[2],
                "lastname": row[3],
                "email": row[4],
                "tel": row[5],
                "created": row[6],
                "faces": [],
            }
        # user["faces"].append(face)
        if 7 in row:
            user["faces"].append(face)
        index = index + 1

    if 'id' in user:
        return user
    return None


def delete_user_by_id(user_id):
    app.db.delete('DELETE FROM users WHERE users.id = ?', [user_id])
    # also delete all faces with user id
    app.db.delete('DELETE FROM faces WHERE faces.user_id = ?', [user_id])

#   Route for Hompage
@app.route('/', methods=['GET'])
def page_home():

    return render_template('index.html')

# api version
@app.route('/api', methods=['GET'])
def api_version():
    output = json.dumps({"api": '1.0'})
    return success_handle(output)

# train
@app.route('/api/train', methods=['POST'])
def train():
    output = json.dumps({"success": True})

    if 'file' not in request.files:
        print ("Face image is required")
        return error_handle("Face image is required.")
    else:
        print("File request", request.files)
        file = request.files['file']

        if file.mimetype not in app.config['file_allowed']:
            print("File extension is not allowed")
            return error_handle("Only allow upload file with *.png , *.jpg")
        else:
            # get parameter from form data
            username = request.form['username']
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            password = request.form['password']
            email = request.form['email']
            tel = request.form['tel']

            print("Information of that face", username)


            print("File is allow and will be saved in ", app.config['storage'])
            filename = secure_filename(file.filename)

            trained_storage = path.join(app.config['storage'], 'trained')
            file.save(path.join(trained_storage, filename))
            # save file to storage

            # save to sqlite database.db
            created = int(time.time())
            user_id = app.db.insert('INSERT INTO users(username, firstname, lastname, password, email, tel, created) values(?, ?, ?, ?, ?, ?, ?)',[username, firstname, lastname, password, email, tel, created])

            if user_id:
                print("User saved in data", username, user_id)
                # user has been save with user_id and now we need save faces table as well

                face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) values(?, ?, ?)', [user_id, filename, created])

                if face_id:
                    print("Cool face has been saved.")
                    face_data = {"id": face_id, "filename": filename, "created": created}
                    return_output = json.dumps({"id": user_id, "username": username, "face": [face_data]})
                    return success_handle(return_output)
                else:
                    print ("An error saving face image.")
                    return error_handle("An error saving face image.")

            else:
                print("Something happened")
                return error_handle("An error inserting new user")
        print("Request is contain image")
    return success_handle(output)


@app.route('/api/recognize', methods=['POST'])
def recognize():
    if 'file' not in request.files:
        return error_handle("Image is required")
    else:
        file = request.files['file']
        filename = secure_filename(file.filename)

        # file extension validate
        if file.mimetype not in app.config['file_allowed']:
            return error_handle("File extension is not allowed")
        else:
            filename = secure_filename(file.filename)
            unknown_storage = path.join(app.config["storage"], 'unknown')
            file_path = path.join(unknown_storage, filename)
            file.save(file_path)

            user_id = app.face.recognize(filename)
            if user_id:
                user = get_user_by_id(user_id)
                message = {"message": "Hey we found {0} matched with your face image".format(user["username"]),
                           "user": user}
                return success_handle(json.dumps(message))
            else:
                return error_handle("Sorry we can not found any people matched with your face image, try another image")

    return success_handle(json.dumps({"filename_to_compare_is": filename }))


@app.route('/api/users/<int:user_id>', methods=['GET', 'DELETE'])
def user_profile(user_id):
    if request.method == 'GET':
        user = get_user_by_id(user_id)
        if user:
            return success_handle(json.dumps(user), 200)
        else:
            return error_handle("User not found", 404)
    if request.method == 'DELETE':
        delete_user_by_id(user_id)
        return success_handle(json.dumps({"deleted": True}))


# Register process
@app.route('/api/regist_face', methods=['POST'])
def registration():
    message = "success"

    username = request.form['username']
    

    # create directory for this username inorder to save image Before croped
    create_directory_before_crop_images(username)

    # create directory for this username inorder to save image After croped
    create_directory_after_crop_images(username)

    before_crop_image_dir = path.join ( app_path, "storage/pre_croped_images/"+username)
    upload_to_before_crop_images(username)

    # process croping face an image
    crop_face_process(username,before_crop_image_dir)

    # train
    message = train_model()

    # return success_handle(json.dumps(message))
    return message


@app.route('/api/predict/<string:ref>', methods=['POST'])
def predict_person(ref):
    send_time = int(time.time())
    image_id = "{}{}".format(ref, send_time)
    str = encode_base64("obama.jpg")
    test_pic_dir = decode_base64(str, image_id)

    predict_message = app.recognizer.predictor_face(test_pic_dir)
    # predict_message = {"predict_person": predict_person}
    return success_handle(json.dumps(predict_message))


# encodeB64
@app.route('/encodeB64', methods=['GET'])
def encodeB64():
    str = encode_base64("obama.jpg")
    print(encode_base64("obama.jpg"))
    return str


# Run the app
app.run()
