from flask import Flask, render_template, Response, request, redirect, url_for
from simple_salesforce import Salesforce
import cv2
import face_recognition
import numpy as np
from flask import session
import pickle
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://your-salesforce-domain.com"}})
app.config['SECRET_KEY'] = 'mysecretkey' 

def generate_frame():
    camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    camera.release()
    if not ret:
        return None
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(frame_rgb)
    face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)
    if face_encodings:
        return face_encodings[0]
    else:
        return None


def verify_face(face_encoding):
    if 'sf' not in session:
        return False
    sf = pickle.loads(session['sf'])

    try:
        # Query
        query_string = "SELECT Id, Face_data__c FROM User_Account__c"
        query_result = sf.query_all(query_string)
        for record in query_result['records']:
            user_id = record['Id']
            known_face_encoding = np.fromstring(record['Face_data__c'], dtype=float, sep=' ')
            matches = face_recognition.compare_faces([known_face_encoding], face_encoding)
            if matches[0]:
                redirect_url = f"https://dhp000001qvqpmay-dev-ed.develop.lightning.force.com/lightning/r/User_Account__c/{user_id}/view"
                return redirect(redirect_url)
        return redirect(url_for('failure'))
        
    except Exception as e:
        print(str(e)) 
        return redirect(url_for('failure'))
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    security_token = request.form['security_token']
    faceRecognition = request.form.get('faceRecognition', 'off')

    try:
        sf = Salesforce(username=username, password=password, security_token=security_token)
        session['sf'] = pickle.dumps(sf)
        if faceRecognition == 'on':
            return redirect(url_for('capture'))
        else:
            return "Face recognition can't be performed if camera access is not granted.", 400
    except Exception as e:
        return str(e)

@app.route('/capture')
def capture():
    
    face_array = generate_frame()
    if face_array is None:
        return "Could not capture the image", 500
    else:
        return verify_face(face_array)


@app.route('/success')
def success():
    return "Login Successful!"

@app.route('/failure')
def failure():
    return "Login Failed!"


if __name__ == '__main__':
    app.run(debug=True)