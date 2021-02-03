import json
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from flask import Flask,jsonify

import google.cloud.logging
import requests
from bs4 import BeautifulSoup
from google.cloud import datastore, pubsub_v1
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

## Application Variables
LoggingClient = google.cloud.logging.Client()
CourseList = []
RequiredTimes = []
DaysOfWeek = []

## Get Envars
project_id = os.environ.get('GCP_PROJECT', '')
topic_name = os.environ.get('pubsub_topic', 'golf-bot-notify')

# App Config
app = Flask(__name__)

# Function To Send Ttxt
def send_sms(DataTosend):
    # Publish Message to PubSub Queue to Notify
    global project_id,topic_name

    NotificationTypes = GetNotificationTimes()
    startTime = datetime.combine(date.today(),datetime.strptime(NotificationTypes['start'], '%H:%M').time())
    startTime.replace(tzinfo=timezone.pst)
    endTime = datetime.combine(date.today(),datetime.strptime(NotificationTypes['end'], '%H:%M').time())
    endTime.replace(tzinfo=timezone.pst)

    # Notifications Disabled
    if not NotificationTypes['enabled']:
        return

    # Check if now is between notification times
    RightNow = datetime.now()
    RightNow.replace(tzinfo=timezone.pst)
    if startTime <= RightNow <= endTime:
        logging.info("Inside Notification Window")
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic_name)
        future = publisher.publish(topic_path, DataTosend.encode("utf-8"))
    else:
        logging.info("Outside Notification Window")

# Function To Get Notification Times from DataStore
def GetNotificationTimes():
    global project_id

    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="notificationTimes")
    results = list(query.fetch())
    return({"start":results[0]['start'],"end":results[0]['end'], "enabled" : results[0]['enabled']})

# Function To Get Course List From Datastore
def GetCourseList():
    global project_id
    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="Locations")
    datastore_values = list(query.fetch())
    results = []
    for aSet in datastore_values:
        aResult = { "Name" : aSet['Name'], "Location": aSet['Location'], "KeyElement" : aSet['KeyElement'], "Course" : aSet['Course']}
        results.append(aResult)
    
    return results

# Function To Get Notification Times from DataStore
def GetSearchTimes():
    global project_id
    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="searchTimes")
    results = list(query.fetch())
    return({"start":results[0]['teeTimeStart'],"end":results[0]['teeTimeEnd']})

# Function To Get Day Of Week from Datastore
def GetDayOfWeek():
    global project_id
    # Now try to load the keys from DS:
    query = datastore.Client(project=project_id,namespace='golf-bot').query(kind="Options")
    results = list(query.fetch())

    return(list(map(int,results[0]['DaysOfWeek'].split(','))))

# Function To Save Times to Datastore
def SaveFoundTimesToDataStore(Location: str, TimesToSave, Notified: bool):
    global project_id
    # Create a Cloud Datastore client.
    datastore_client = datastore.Client(project=project_id,namespace='golf-bot')
    # Create the Cloud Datastore key for the new entity.
    kind = "TeeTimesFound"
    name = Location
    task_key = datastore_client.key(kind,name)
    task = datastore.Entity(key=task_key)
    task['notify'] = Notified
    task['times'] = { 'values' : TimesToSave }

    datastore_client.put(task)

# Get values from Datastore
def GetFoundTimes(Location: str):
    global project_id
    # Now try to load the keys from DS:
    client = datastore.Client(project=project_id,namespace='golf-bot')
    key = client.key("TeeTimesFound", Location)
    
    query = client.get(key)
    if query:
        print(query['times'])
        return(query['times'])
    else:
        return([])

# Function To Get Next X day of the week
def GetNextDate(DayOfWeek):
    ## Input Values
    ## 0 Monday - 6 Sunday
    ## Output Values
    ## Date of next given DOW, formated 10/12/2020

    d = datetime.now()
    while d.weekday() != DayOfWeek:
        d = d + timedelta(days=1)

    # Return the format    
    return d.strftime('%m/%d/%Y')

# Function to build out the search times
def BuildSearchTimes():
    # Get start and end values from DataStore
    SearchTimes = GetSearchTimes()
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

# Function to compare lists
def Diff(li1, li2):
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2]
    return li_dif

# Send notification of date Found
def Notify(NumSlotsFound,FoundRanges,DateFound):
    # Notification process
    ## SendSMS validates timeframe for communication
    ## This function looks for values to notify on



    # First check if any existing values have been notified for:
    for aRange in FoundRanges:
        # Build txt body:
        Body = f"Found {str(NumSlotsFound)} slot(s) on the following date {str(DateFound)} for {aRange}:"
        datastoreValues = GetFoundTimes(Location=aRange)
        Body += "\n" + str(FoundRanges[aRange])

        ### TODO FIX THIS MESS
        # If Empty add them all and save to DataStore
        # if not datastoreValues:
        #     Body += "\n" + str(FoundRanges[aRange])
        # else:
        #     #Now need to compare and save the new range to dataStore
        #     TimesNowNotAvailable = Diff(list(FoundRanges[aRange]),datastoreValues)
        #     Body += "\n Times not available anymore: " + str(TimesNowNotAvailable)
        #     print(TimesNowNotAvailable)
        #     TimesNowAvailable = Diff(datastoreValues,list(FoundRanges[aRange]))
        #     Body += "\n New Times available : " + str(TimesNowAvailable)
        #     print(TimesNowNotAvailable)

        # Save the new time slots to Datastore
        SaveFoundTimesToDataStore(Location=aRange,TimesToSave=str(FoundRanges[aRange]),Notified=True)
        
        # Log Txt Body
        logging.info(f"Sending Txt Message with the following details: {Body}")

        # Send SMS Notification
        send_sms(DataTosend=Body)

# Function to find the slots availble on the return value
def FindTimes(InputPage,aCourse=""):
    global RequiredTimes
    # Foreach time slot in RequiredTimes look for that text in the page, if found return the value
    results = []

    if aCourse == "" or aCourse == "*":
        ## Itterate over values for any course
        for aTimeSlot in RequiredTimes:
            # look for time slots
            if aTimeSlot in InputPage:
                # Time slot found!
                results.append(aTimeSlot)
    else:
        # Load Page into Beautiful Soup to find values
        soup = BeautifulSoup(InputPage, 'html.parser')
        # Each slot is a list item (li). Itterate through li's
        for li in soup.findAll('li'):
            # Now Itterate over times and find matching course title
            for aTimeSlot in RequiredTimes:
                # look for time slots
                if (str(aTimeSlot) in li.text) and (aCourse in li.text):
                    # Time slot found!
                    results.append(aTimeSlot)

    ## Return found list
    return results

# Function To load the page with target data
def LoadPage(TargetPage, TargetDate, KeyElement):
    # Todo: Build Selinum bot to open page one then submit
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--no-sandbox")
    browser = webdriver.Chrome(options=chrome_options)

    #Load Page
    browser.get(TargetPage)
    time.sleep(1)

    #If redirected to /preSearch then hit submit
    currentURL = browser.current_url
    if currentURL.find("preSearch") != -1:
        time.sleep(1)
        btnSubmit = browser.find_element_by_xpath("//button[contains(@class,'btn')]")
        btnSubmit.click()
        time.sleep(2)
        btnSubmit = browser.find_element_by_xpath("//button[contains(@class,'btn')]")
        btnSubmit.click()
        time.sleep(1)

    DatePicker = browser.find_element_by_id(KeyElement)
    DatePicker.clear()
    DatePicker.send_keys(TargetDate)
    DatePicker.send_keys(Keys.RETURN)
    # Wait until data loaded
    time.sleep(1)
    return browser.page_source

# Main Loop
@app.route("/", methods=['GET'])
def Main():
    global DaysOfWeek, RequiredTimes, CourseList
    # Main Function

    # Setup the logger
    LoggingClient.get_default_handler()
    LoggingClient.setup_logging()

    # Get Search Values from Datastore
    DaysOfWeek = GetDayOfWeek()
    RequiredTimes = BuildSearchTimes()
    CourseList = GetCourseList()
    print(CourseList)
    # Itterate through Course
    for aCourse in CourseList:
        # Itterate over Days of the week to search
        DaysOfWeek.sort()
        for aDay in DaysOfWeek:
            ## Variable for Next TargetDate
            NextDate = GetNextDate(aDay)
            logging.info(f"Checking the site: {aCourse['Location']}. Looking for the following Tee Times {RequiredTimes} on the date: {NextDate}, for {aCourse['Course']} course(s).")

            # Check the page content & Pass it for validation
            FoundTimeSlots = {}
            if aCourse["Course"] == "*":
                ## Load the page and return the value
                ReturnedPage = LoadPage(TargetPage=aCourse["Location"], TargetDate=NextDate,KeyElement=aCourse["KeyElement"])
                ## Now Check for found time
                FoundTimeSlots[aCourse["Name"]] = FindTimes(InputPage=ReturnedPage)
            else:
                # Itterate over course
                for aSubCourse in aCourse["Course"]:
                    ## Load the page and return the value
                    ReturnedPage = LoadPage(TargetPage=aCourse["Location"], TargetDate=NextDate,KeyElement=aCourse["KeyElement"])
                    aResultSet = FindTimes(InputPage=ReturnedPage,aCourse=aSubCourse)
                    # Validate there are times found
                    if aResultSet:
                        FoundTimeSlots[aSubCourse] = aResultSet
            
            ## Check if any found
            NumOfSlotsFound = 0
            for aKey in FoundTimeSlots:
                if FoundTimeSlots[aKey]:
                    NumOfSlotsFound += len(FoundTimeSlots[aKey])

            if NumOfSlotsFound > 0:
                ## Some Values found, sending txt
                logging.info (f"Found {NumOfSlotsFound} times: {FoundTimeSlots}, on {NextDate}")
                Notify(NumOfSlotsFound, FoundTimeSlots,NextDate)
            else:
                logging.info (f"Found {NumOfSlotsFound} times")
            
            ## End

    return jsonify(success=True)

if __name__ == "__main__":
   ## Run APP
    app.run(host='0.0.0.0', port=8080)
    
