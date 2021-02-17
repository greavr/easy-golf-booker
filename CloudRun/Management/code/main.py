import requests
from flask import Flask, flash, redirect, render_template, request
import os
from google.cloud import datastore
import google.cloud.logging

# App Config
app = Flask(__name__)

# DataStore value map
ValueMap = [{'players':'Options'},{'DaysOfWeek':'Options'},{'Numbers':'notificationTimes'},{'Enabled':'notificationTimes'},{'start':'notificationTimes'},{'end':'notificationTimes'},{'teeTimeStart':'searchTimes'},{'teeTimeEnd':'searchTimes'}]

## Get Envars
project_id = os.environ.get('GCP_PROJECT', '')

NotificationTimes = []
CourseList = []
SearchTimes = []
DaysOfWeek = []
Players = []

# Function To Get Notification Times from DataStore
def GetNotificationTimes():
    global project_id

    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="notificationTimes")
    results = list(query.fetch())
    return({"start":results[0]['start'],"end":results[0]['end'], "enabled" : results[0]['enabled'], "Numbers" : results[0]['Numbers'], "timezone" : results[0]['timezone']})

# Function To Get Course List From Datastore
def GetCourseList():
    global project_id, CourseList
    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="Locations")
    datastore_values = list(query.fetch())
    results = []
    for aSet in datastore_values:
        aResult = { "Name" : aSet['Name'], "Location": aSet['Location'], "KeyElement" : aSet['KeyElement'], "Course" : aSet['Course']}
        results.append(aResult)
    
    return(results)

# Function To Get Notification Times from DataStore
def GetSearchTimes():
    global project_id, SearchTimes
    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="searchTimes")
    results = list(query.fetch())
    return({"start":results[0]['teeTimeStart'],"end":results[0]['teeTimeEnd']})

# Function To Get Day Of Week from Datastore
def GetOptions():
    global project_id, DaysOfWeek, Players
    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="Options")
    results = list(query.fetch())

    return(results)
    #DaysOfWeek = list(map(int,results[0]['DaysOfWeek'].split(',')))
    #Players = list(map(int,results[0]['Players'].split(',')))

# Function to save value to DataStore
def SaveValue(ValueName: str, ValueItem: str, DataStoreKind: str):
    pass

# Function to load values from DataStore
def GetValues():
    global NotificationTimes, CourseList, SearchTimes, DaysOfWeek,Players
    NotificationTimes = GetNotificationTimes()
    CourseList = GetCourseList()
    SearchTimes = GetSearchTimes()
    AllOptions = GetOptions()
    DaysOfWeek = list(map(int,AllOptions[0]['DaysOfWeek'].split(',')))
    Players = list(map(int,AllOptions[0]['Players'].split(',')))
    print(f"{NotificationTimes}, {CourseList}, {SearchTimes}, {DaysOfWeek}, {Players}")

#API EndPoint
@app.route("/save", methods=['POST'])
def save(valuesToSave=[]):
    # Lookup where to save relative values
   pass

# Function to refresh the page
@app.route("/load", methods=['GET'])
def load():
    pass

#Edit Values Handler
@app.route("/edit", methods=['GET','POST'])
def edit():
    global NotificationTimes, CourseList, SearchTimes, DaysOfWeek,Players
    GetValues()
    return render_template('edit.html', Notification_Times=NotificationTimes, Course_List=CourseList, Search_Times=SearchTimes, Days_Of_week=DaysOfWeek,Player_Count=Players )

#Main Function handler
@app.route("/", methods=['GET'])
def main():

    return render_template('index.html')

if __name__ == "__main__":
    ## Run APP
    app.run(host='0.0.0.0', port=8080)