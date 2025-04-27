from flask import Flask, render_template, request
from datetime import date, timedelta
import matplotlib.pyplot as plt
from PIL import Image
import urllib3
import json
import os, io
from io import StringIO
import base64
import time

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from flask import Flask, render_template, request, redirect, url_for, session
import json
from werkzeug.security import check_password_hash, generate_password_hash

app= Flask(__name__)
app.secret_key = 'your_secret_key'

#cred = credentials.Certificate("secret.json")
cred_dict = json.loads(os.environ["FIREBASE_CREDENTIALS"])
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()
#print("CONNECTED!")

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Initialize error variable

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with open('users.json', 'r') as file:
            users = json.load(file)

        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password'  # Set error message

    return render_template('login.html', error=error)

'''
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password == confirm_password:
            hashed_password = generate_password_hash(password)

            with open('users.json', 'r') as file:
                users = json.load(file)

            users[username] = {'password': hashed_password}

            with open('users.json', 'w') as file:
                json.dump(users, file)

            return render_template('signup_success.html', username=username)

        else:
            return render_template('signup.html', error='Passwords do not match')

    return render_template('signup.html')
'''
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/trigger_reset', methods=['POST'])
def trigger_reset():
    # Your Python function goes here
    
    update_override_values(True, False)
    ##print("RESET BUTTON CLICKED!.")
    return redirect(url_for('dashboard'))

@app.route('/trigger_set', methods=['POST'])
def trigger_set():
    # Your Python function goes here
    
    update_override_values(False, True)
    ##print("SET BUTTON CLICKED!.")
    return redirect(url_for('dashboard'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/timetravel.html")
def timetravel():
    return render_template('timetravel.html')

@app.route("/timetravel.html", methods=['POST'])
def read_data(intersection_id="Intersection 1", lane_id="Lane 1"):
    
    vehicles_count = []
    timestamp = []
    data = []

    if request.method == 'POST':
        requested_intersection = request.form['intersectioninput']
        requested_lane = request.form['laneinput']
        requested_day = request.form['dayinput']
        
    try:
        collection_path = 'Traffiq/'+ requested_intersection + '/'+ requested_lane
        #print(requested_intersection, requested_lane)
        collection_ref = db.collection(collection_path)
        docs = collection_ref.stream()

        for doc in docs:
            data.append(doc.to_dict()) # Convert each document to a dictionary
        #print(data)
        #return data

    except Exception as e:
        #print(f"An error occurred: {e}")
        #return []
    
    #print("DATA", data)
    try:
        for x in data:
            #print("X:", x)
            current_index = 0
            if (requested_day == str(x['time'])[:10]):
                if str(x['time'])[:16] not in timestamp:
                    timestamp.append(str(x['time'])[:16])
                    vehicles_count.append(int(x['vehicles']))
                    current_index = current_index + 1
                else:
                    vehicles_count[current_index-1] +=  int(x['vehicles'])
    except:
        #print("No data in Firestore")
    
    #print("YES", vehicles_count)
    #print(timestamp)
    '''
    for x in data:
        current_index = 0
        #print(str(x['time'])[:16])
        if str(x['time'])[:16] not in timestamp:
            timestamp.append(str(x['time'])[:16])
            vehicles_count.append(int(x['vehicles']))
            current_index = current_index + 1
        else:
            vehicles_count[current_index-1] +=  int(x['vehicles'])
    '''
    if (len(timestamp) != 0):
        return render_template('timetravelresults.html', link=timestamp, top = timestamp, view = vehicles_count, number = len(timestamp), requested_day = requested_day)
    else:
        return render_template("exceptions.html")

@app.route('/recent')
def recent():
    
    vehicles_count = []
    timestamp = []
    data = []
    
    try:
        collection_path = 'Traffiq/' + "Intersection 1" + '/' + "Lane 1"
        collection_ref = db.collection(collection_path)
        query = collection_ref.order_by("time", direction=firestore.Query.DESCENDING)

        docs = query.stream()
        for doc in docs:
            data.append(doc.to_dict())
            #print(f"{doc.id} => {doc.to_dict()}")
    
        #print("STREAM", data)
        
        '''collection_path = 'Traffiq/'+ "Intersection 1" + '/'+ "Lane 1"
        collection_ref = db.collection(collection_path)
        docs = collection_ref.stream()

        for doc in docs:
            data.append(doc.to_dict()) # Convert each document to a dictionary
        ##print(data)
        #return data'''

    except Exception as e:
        #print(f"An error occurred: {e}")
        #return []

    for x in data:
        current_index = 0
        if ((str(x['time'])[:10] not in timestamp) and len(timestamp) <= 6):
            timestamp.append(str(x['time'])[:10])
            vehicles_count.append(int(x['vehicles']))
            current_index = current_index + 1
        else:
            vehicles_count[current_index-1] +=  int(x['vehicles'])

    #print("TIMESTAMPS:",timestamp)
    
    plt.figure(figsize=(10, 10))
    bar = plt.bar(timestamp, vehicles_count)
    plt.title('Total traffic in the last 7 days')
    bar[0].set_color('r')
    bar[1].set_color('g')
    bar[2].set_color('b')
    bar[3].set_color('c')
    bar[4].set_color('m')
    bar[5].set_color('y')
    bar[6].set_color('k')
    plt.legend((bar[0], bar[1], bar[2], bar[3], bar[4], bar[5], bar[6]), (
    timestamp[0], timestamp[1], timestamp[2], timestamp[3], timestamp[4], timestamp[5],
    timestamp[6]), loc="upper right")
    plt.ylabel('Total traffic')
    plt.xlabel('Days')
    ax=plt.gca()
    ax.axes.xaxis.set_ticks([])
    buf=io.BytesIO()
    plt.savefig(buf, bbox_inches='tight')
    buf.seek(0)
    image33=Image.open(buf)
    img_io=io.BytesIO()
    image33.save(img_io,'png')
    img_io.seek(0)
    img = base64.b64encode(img_io.getvalue())

    if 'username' in session:
        #return render_template('dashboard.html', username=session['username'])
        return render_template('recent.html', list_of_topics=timestamp, view = vehicles_count, number = len(timestamp), img=img.decode('ascii'))
    else:
        return redirect(url_for('login'))

    #else:
    #return redirect(url_for('login'))

@app.route('/recent', methods=['POST'])
def custom_recent():
    
    vehicles_count = []
    timestamp = []
    data = []
    

    if request.method == 'POST':
        requested_intersection = request.form['intersectioninput']
        requested_lane = request.form['laneinput']
               
    try:
        collection_path = 'Traffiq/' + requested_intersection + '/' + requested_lane
        collection_ref = db.collection(collection_path)
        query = collection_ref.order_by("time", direction=firestore.Query.DESCENDING)

        docs = query.stream()
        for doc in docs:
            data.append(doc.to_dict())
            ##print(f"{doc.id} => {doc.to_dict()}")
    
        ##print("STREAM", data)
        
        '''collection_path = 'Traffiq/'+ "Intersection 1" + '/'+ "Lane 1"
        collection_ref = db.collection(collection_path)
        docs = collection_ref.stream()

        for doc in docs:
            data.append(doc.to_dict()) # Convert each document to a dictionary
        ##print(data)
        #return data'''

    except Exception as e:
        #print(f"An error occurred: {e}")
        #return []

    for x in data:
        current_index = 0
        #print(x)
        if ((str(x['time'])[:10] not in timestamp) and len(timestamp) <= 7):
            timestamp.append(str(x['time'])[:10])
            vehicles_count.append(int(x['vehicles']))
            current_index = current_index + 1
        else:
            vehicles_count[current_index-1] +=  int(x['vehicles'])

    #print("TIMESTAMPS:",timestamp)
    #print("VEH", vehicles_count)
    plt.figure(figsize=(10, 10))
    bar = plt.bar(timestamp, vehicles_count)
    plt.title('Total traffic in the last 7 days')
    bar[0].set_color('r')
    bar[1].set_color('g')
    bar[2].set_color('b')
    bar[3].set_color('c')
    bar[4].set_color('m')
    bar[5].set_color('y')
    bar[6].set_color('k')
    plt.legend((bar[0], bar[1], bar[2], bar[3], bar[4], bar[5], bar[6]), (
    timestamp[0], timestamp[1], timestamp[2], timestamp[3], timestamp[4], timestamp[5],
    timestamp[6]), loc="upper right")
    plt.ylabel('Total traffic')
    plt.xlabel('Days')
    ax=plt.gca()
    ax.axes.xaxis.set_ticks([])
    buf=io.BytesIO()
    plt.savefig(buf, bbox_inches='tight')
    buf.seek(0)
    image33=Image.open(buf)
    img_io=io.BytesIO()
    image33.save(img_io,'png')
    img_io.seek(0)
    img = base64.b64encode(img_io.getvalue())

    if 'username' in session:
        #return render_template('dashboard.html', username=session['username'])
        return render_template('recent.html', list_of_topics=timestamp, view = vehicles_count, number = len(timestamp), img=img.decode('ascii'))
    else:
        return redirect(url_for('login'))

    #else:
    #return redirect(url_for('login'))

def update_override_values(master_reset_value, master_set_value):
    doc_ref = db.collection("Traffiq").document("Override")

    try:
        doc_ref.update({
            "Master Reset": master_reset_value,
            "Master Set": master_set_value,
        })
        #print("Successfully updated 'master reset' and 'master set' values.")
        #print("Set", master_reset_value, master_set_value)
    except Exception as e:
        #print(f"An error occurred: {e}")
        
if __name__=="__main__":
    app.run(debug=True)
