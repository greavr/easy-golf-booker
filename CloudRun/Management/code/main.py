import json
import os

import google.cloud.logging
import requests
from flask import Flask, flash, redirect, render_template, request
from google.cloud import datastore

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
LastUpdateTimeStamp = ""

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

# Function To Get Log Data
def GetLogData():
    global project_id
    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="TeeTimeLog")
    query.order = ["CourseName"]
    results = list(query.fetch())

    # Organize date for results
    ResultsSet = {}

    for aResult in results:
        # Check for new course
        if aResult["CourseName"] not in ResultsSet:
            ResultsSet[aResult["CourseName"]] = []
        # Add all non-Name attributes as a new list
        ResultsSet[aResult["CourseName"]].append({"CourseName":aResult["CourseName"], "Date": aResult["Date"], "PlayerCount": aResult["PlayerCount"], "Times": aResult["Times"] })

    return(ResultsSet)

# Function To Get Latest data
def GetLatestTime():
    global project_id, LastUpdateTimeStamp
    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="TeeTimesFound")
    results = list(query.fetch())

    # Organize date for results
    ResultsSet = {}

    for aResult in results:
        print(aResult)
        # Check for new course
        if aResult not in ResultsSet:
            ResultsSet[aResult] = []

        # Itterate Through list
        for aArray in aResult["Data"]:
            ResultsSet[aResult].append({"Date": aArray["Date"], "PlayerCount": aArray["PlayerCount"], "Times": aArray["Times"] })
        
        LastUpdateTimeStamp = aResult["TimeStamp"]

    return(ResultsSet)

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

# Logs
@app.route("/logs", methods=['GET','POST'])
def GetLogs():
    DataStoreLogData = GetLogData()
    return render_template('logs.html',LogData=DataStoreLogData)

# Function to refresh the page
@app.route("/about", methods=['GET'])
def about():
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
    # Get the latest values
    global LastUpdateTimeStamp
    LatestTimesFound = GetLatestTime()
    print(LatestTimesFound)

    return render_template('index.html', LastUpdateTime=LastUpdateTimeStamp, FoundTimes=LatestTimesFound)

if __name__ == "__main__":
    ## Run APP
    app.run(host='0.0.0.0', port=8080)
