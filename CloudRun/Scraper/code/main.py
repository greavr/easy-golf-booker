import collections
import json
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

import google.cloud.logging
import pytz
from pytz import reference
import requests
from flask import Flask, jsonify
from google.cloud import datastore, pubsub_v1

from golfcourse import golfcourse

## Application Variables
LoggingClient = google.cloud.logging.Client()
GolfCourseList = []

## Get Envars
project_id = os.environ.get('GCP_PROJECT', '')
topic_name = os.environ.get('pubsub_topic', 'golf-bot-notify')

# App Config
app = Flask(__name__)

# Function To Send Ttxt
def send_sms(DataTosend):
    # Publish Message to PubSub Queue to Notify
    global project_id,topic_name

    #Set TimeZone
    NotificationTypes = GetNotificationTimes()
    timezone = pytz.timezone(NotificationTypes['timezone'])

    startTime = datetime.combine(date.today(),datetime.strptime(NotificationTypes['start'], '%H:%M').time())
    startTime = timezone.localize(startTime)
    endTime = datetime.combine(date.today(),datetime.strptime(NotificationTypes['end'], '%H:%M').time())
    endTime = timezone.localize(endTime)

    # Notifications Disabled
    if not NotificationTypes['enabled']:
        return

    # Check if now is between notification times
    RightNow = datetime.now()
    RightNow = timezone.localize(RightNow)

    print(f"ST: {startTime}, ET: {endTime}, RN: {RightNow}, RN-NO-TZ: {datetime.now()}, TimeZone: {reference.LocalTimezone().tzname(datetime.now())}")

    if startTime <= RightNow <= endTime:
        logging.info("Inside Notification Window")
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic_name)
        future = publisher.publish(topic_path, DataTosend.encode("utf-8"))
    else:
        logging.info("Outside Notification Window")

# Send notification of date Found
def Notify(NumSlotsFound,FoundRanges,DateFound, Course, Players):
    # Notification process
    ## SendSMS validates timeframe for communication
    ## This function looks for values to notify on
    if NumSlotsFound == 0:
        return

    # Build txt body:
    Body = f"Found {str(NumSlotsFound)} slot(s) on the following date {str(DateFound)} for {Players} players at {Course}:"
    Body += "\n" + str(FoundRanges)
    # Log Txt Body
    logging.info(f"Sending Txt Message with the following details: {Body}")

    # Send SMS Notification
    send_sms(DataTosend=Body)

# Function To Build GolfCourse Object
def BuildGolfCourseList():
    global GolfCourseList
    # Get Search Times
    AllSearchTimes = BuildSearchTimes()
    AllOptions = GetOptions()

    # Get Course List from Datastore
    CourseList = GetCourseList()
    
    #Build Array Of GolfCourse Objects
    for aLocation in CourseList:
        thisGolf = golfcourse(LocationName=aLocation["Name"],CourseURL=aLocation["Location"], CourseNames=aLocation["Course"], SearchTimes=AllSearchTimes, PlayerElement=aLocation["PlayerElement"], DateElement=aLocation["DateElement"], SearchDates=AllOptions["DaysOfWeek"], SearchPlayers=AllOptions["Players"])
        GolfCourseList.append(thisGolf)

# Function To Get Notification Times from DataStore
def GetNotificationTimes():
    global project_id

    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="notificationTimes")
    results = list(query.fetch())
    return({"start":results[0]['start'],"end":results[0]['end'], "enabled" : results[0]['enabled'], "timezone" : results[0]['timezone']})

# Function To Get Course List From Datastore
def GetCourseList():
    global project_id
    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="Locations")
    datastore_values = list(query.fetch())
    results = []
    for aSet in datastore_values:
        aResult = { "Name" : aSet['Name'], "Location": aSet['Location'], "DateElement" : aSet['DateElement'], "Course" : aSet['Course'], "PlayerElement" : aSet['PlayerElement']}
        results.append(aResult)
    
    return results

# Function To Get Day Of Week from Datastore
def GetOptions():
    global project_id
    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="Options")
    results = list(query.fetch())
    return(results[0])
    #return({"Days" : list(map(int,results[0]['DaysOfWeek'].split(','))), "Players" : list(map(int,results[0]['Players'].split(','))) })

# Function To Save Times to Datastore
def SaveFoundTimesToDataStore(Location, DataToSave):
    global project_id

    namespace='golf-bot'
    kind = "TeeTimesFound"

    #Create Array of data elements
    DataToAdd = []
    for aDataRow in DataToSave:
        DataToAdd.append({ 'PlayerCount' : aDataRow["PlayerCount"], "Times": aDataRow['Times'], "Date": aDataRow["Date"] })

    try:
        # Create a Cloud Datastore client.
        datastore_client = datastore.Client(project=project_id,namespace=namespace)
        # Create the Cloud Datastore key for the new entity.
        task_key = datastore_client.key(kind,Location)
        task = datastore.Entity(key=task_key)
        task['Data'] = DataToAdd
        task['TimeStamp'] = datetime.now()
        datastore_client.put(task)
    except:
        e = sys.exc_info()
        logging.error(f"Error Occured: {e}, Project: {project_id}, NameSpace: {namespace}, Kind: {kind}, Name: {Location}, Data: {DataToSave}")

# Get values from Datastore
def GetFoundTimes(Location: str):
    global project_id
    # Now try to load the keys from DS:
    client = datastore.Client(project=project_id,namespace='golf-bot')
    key = client.key("TeeTimesFound", Location)
    
    query = client.get(key)
    if query:
        return(query['Data'])
    else:
        return([])

# Function to build out the search times
def BuildSearchTimes():
    # Get start and end values from DataStore
    global project_id
    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="searchTimes")
    results = list(query.fetch())
    SearchTimes = {"start":results[0]['teeTimeStart'],"end":results[0]['teeTimeEnd']}

    # Create array of times
    startTime = datetime.strptime(SearchTimes['start'], '%H:%M').time()
    endTime = datetime.strptime(SearchTimes['end'], '%H:%M').time()

    # Create array of times between the two
    step = timedelta(minutes=1)
    seconds = (datetime.combine(date.today(), endTime) - datetime.combine(date.today(), startTime)).total_seconds()
    array = []
    for i in range(0, int(seconds), int(step.total_seconds())):
        array.append(datetime.combine(date.today(), startTime) + timedelta(seconds=i))
    
    # Format Array
    array = [i.strftime('%-I:%M %p') for i in array]
    
    return array

# Main Loop
@app.route("/", methods=['GET'])
def Main():
    global GolfCourseList
    # Main Function

    # Get Search Values from Datastore
    BuildGolfCourseList()

    # Itterate through Course
    for aGolfCourse in GolfCourseList:
        aGolfCourse.FindSpots()

        ## Check if any times found
        if not any(aGolfCourse.FoundTimes):
            logging.info(f"Not times found for {aGolfCourse.LocationName}.")
        else:
            # Ittereate over found 
            for aFoundSet in aGolfCourse.FoundTimes:
                # Recall last search results looking for changes
                PreviousFoundData = GetFoundTimes(aFoundSet)
                ChangesFound = []
                # Compare Results
                if not PreviousFoundData:
                    # No previous results found
                    NewDataSet = aGolfCourse.FoundTimes[aFoundSet]
                    SaveFoundTimesToDataStore(Location=aFoundSet,DataToSave=NewDataSet)
                    # Itterate through sub sets of data
                    for aDataRow in NewDataSet:
                        ChangesFound.append({"Date" : aDataRow["Date"], "Times" : aDataRow["Times"], "NumofSlotsFound" : len(aDataRow["Times"]), "Players" : aDataRow["PlayerCount"]})
                    
                else:
                    # Compare results set
                    JustFoundData = aGolfCourse.FoundTimes[aFoundSet]

                    # Itterate over both lists looking for differences
                    for aNewDataSet in JustFoundData: # New datas
                        for aOldDataSet in PreviousFoundData: # Old datas
                            #Check date & player count
                            if (aOldDataSet["PlayerCount"] == aNewDataSet["PlayerCount"]) and (aOldDataSet["Date"] == aNewDataSet["Date"]):
                                # Check Times Found Lists   
                                if not collections.Counter(aOldDataSet["Times"]) == collections.Counter(aNewDataSet["Times"]):
                                    SaveFoundTimesToDataStore(Location=aFoundSet,DataToSave=aGolfCourse.FoundTimes[aFoundSet])
                                    ChangesFound.append({"Date" : aNewDataSet["Date"], "Times" : aNewDataSet["Times"], "NumofSlotsFound" : len(aNewDataSet["Times"]), "Players" : aNewDataSet["PlayerCount"]})

            # If Changes Found Send TXT
            if len(ChangesFound) > 0:
                # Itterate over found values
                for aResultSet in ChangesFound:
                    if aResultSet['NumofSlotsFound'] > 0:
                        logging.info (f"Found {aResultSet['NumofSlotsFound']}, Times: {aResultSet['Times']}, on {aResultSet['Date']} for {aResultSet['Players']} players.")
                        Notify(NumSlotsFound=aResultSet['NumofSlotsFound'], FoundRanges=aResultSet['Times'],DateFound=aResultSet['Date'],Course=aFoundSet, Players=aResultSet['Players'] )
            else:
                # Found Zero Changes
                logging.info (f"Found {len(ChangesFound)} new times")             


    return jsonify(success=True)

if __name__ == "__main__":
    ## Run APP
    # Setup the logger
    LoggingClient.get_default_handler()
    LoggingClient.setup_logging()
    app.run(host='0.0.0.0', port=8080)
    
