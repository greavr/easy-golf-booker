from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import requests
import json
from datetime import datetime, timedelta, date
import time

## Application Variables
CourseList = [{"Location":"https://hardingpark.ezlinksgolf.com/index.html#/search","Course" : "*","KeyElement" : "pickerDate"},{"Location":"https://coricapark.ezlinksgolf.com/index.html#/preSearch","Course": ["Corica Park - 1. South Course","Corica Park - 2. North Course"],"KeyElement" : "pickerDate" }]
RequiredTimes = ["9:15 AM", "9:30 AM", "9:45 AM"]
NumPlayers = 2
DaysOfWeek = [5,4]

## Application logic
# Load Page
# Look for time values required
# If found send TXT message
# If not found die

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

# Send notification of date Found
def Notify(NumSlotsFound,FoundRange,DateFound):
    # Todo
    ## Notification Policy
    ### Notify Each time zone once and done
    pass

# Function to find the slots availble on the return value
def FindTimes(InputPage,Courses=""):
    # Foreach time slot in RequiredTimes look for that text in the page, if found return the value
    results = []

    if Courses == "" or Courses == "*":
        pass
    else:
        ## Itterate over values for any course
        for aTimeSlot in RequiredTimes:
            # look for time slots
            if aTimeSlot in InputPage:
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
def Main():
    # Main Function
    # Itterate through Course
    for aCourse in CourseList:
        # Itterate over Days of the week to search
        DaysOfWeek.sort()
        for aDay in DaysOfWeek:
            ## Variable for Next TargetDate
            NextDate = GetNextDate(aDay)
            print(f"Checking the site: {aCourse['Location']}. Looking for the following Tee Times {RequiredTimes} on the date: {NextDate}, for {aCourse['Course']} course(s).")

            # Check the page content & Pass it for validation
            FoundTimeSlots = {}
            if aCourse["Course"] == "*":
                ## Load the page and return the value
                ReturnedPage = LoadPage(TargetPage=aCourse["Location"], TargetDate=NextDate,KeyElement=aCourse["KeyElement"])
                ## Now Check for found time
                FoundTimeSlots["*"] = FindTimes(ReturnedPage)
                with open(f"{aCourse['Location'].split('//')[1].split('.')[0]}.html", "w") as file1:
                    file1.write(ReturnedPage) 
            else:
                # Itterate over course
                for aSubCourse in aCourse["Course"]:
                    ## Load the page and return the value
                    ReturnedPage = LoadPage(TargetPage=aCourse["Location"], TargetDate=NextDate,KeyElement=aCourse["KeyElement"])
                    FoundTimeSlots[aSubCourse] = FindTimes(ReturnedPage,aSubCourse)
                    with open(f"{aCourse['Location'].split('//')[1].split('.')[0]}-{aSubCourse}.html", "w") as file1:
                        file1.write(ReturnedPage) 
            
            ## Check if any found
            NumOfSlotsFound = 0
            for aKey in FoundTimeSlots:
                if FoundTimeSlots[aKey]:
                    NumOfSlotsFound += 1

            if NumOfSlotsFound > 0:
                ## Some Values found, sending txt
                print (f"Found {NumOfSlotsFound} times: {FoundTimeSlots}, on {NextDate}")
                Notify(NumOfSlotsFound, FoundTimeSlots,NextDate)
            else:
                print (f"Found {NumOfSlotsFound} times")
            
            ## End

if __name__ == "__main__":
    Main()
