import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import time
import datetime
import pytz

ist = pytz.timezone('Asia/Kolkata')

cred = credentials.Certificate("secret.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

print("CONNECTED!")

def store_data(data, intersection_id, lane_id):

    collection = db.collection('Traffiq')
    intersection_doc_ref = collection.document(intersection_id)
    lane_collection = intersection_doc_ref.collection(lane_id)

    data_item = {
        'time': str(datetime.datetime.now(ist)).replace(24, 23),
        'vehicles': data,
    }
    lane_doc_ref = lane_collection.document(str(datetime.datetime.now(ist)))
    lane_doc_ref.set(data_item)
    print("Added data item")

def manual_update_firestore(intersection_id, lane_id, minute, day):
    ist = pytz.timezone('Asia/Kolkata')

    collection = db.collection('Traffiq')
    intersection_doc_ref = collection.document(intersection_id)
    lane_collection = intersection_doc_ref.collection(lane_id)

    year = 2025
    month = 4
    day = day
    hour = 10 
    minute = minute
    second = 0   

    specific_datetime_ist = datetime.datetime(year, month, day, hour, minute, second, tzinfo=ist)

    data_item = {
        'time': specific_datetime_ist,
        'vehicles': 7
    }

    lane_doc_ref = lane_collection.document(str(specific_datetime_ist))
    lane_doc_ref.set(data_item)
    print("Added data item")


def read_data(intersection_id, lane_id):
    collection_path = 'Traffiq/'+ intersection_id + '/'+lane_id
    try:
        collection_ref = db.collection(collection_path)
        docs = collection_ref.stream()

        data = []
        for doc in docs:
            data.append(doc.to_dict()) # Convert each document to a dictionary
        return data

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def update_override_values(master_reset_value, master_set_value):
    doc_ref = db.collection("TraffiQ").document("Override")

    try:
        doc_ref.update({
            "Master Reset": master_reset_value,
            "Master Set": master_set_value,
        })
        print("Successfully updated 'master reset' and 'master set' values.")
    except Exception as e:
        print(f"An error occurred: {e}")


def ping_firestore_override():
    
    doc_ref = db.collection("Traffiq").document("Override")
    try:
        doc = doc_ref.get()
        if doc.exists:
            override_data = doc.to_dict()
            master_reset = override_data.get('Master Reset')
            master_set = override_data.get('Master Set')

            print(f"Document data: {override_data}")
            print(f"Master Reset: {master_reset}")
            print(f"Master Set: {master_set}")

        else:
            print("No such document!")
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    days = [24, 23, 22, 21, 20, 19, 18, 17]
    for day in days:
        minute = 30
        for i in range(0, 5):
            manual_update_firestore("Intersection 2", "Lane 1", minute, day)
            minute = minute + 1
            time.sleep(1)
    
    #ping_firestore_override()
    '''documents = read_data("Intersection 1", "Lane 1")

    if documents:
        for doc in documents:
            print(doc)  # Print each document
    else:
        print("No documents found in the specified collection.")
    '''

if __name__ == "__main__":
    main()
