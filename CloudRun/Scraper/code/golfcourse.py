import json
import logging
import sys
import time
from datetime import date, datetime, timedelta, timezone

import google.cloud.logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select


class golfcourse:
    # Class to find and store session info
    # Setup Function
    def __init__(self, LocationName, CourseURL, CourseNames, SearchTimes, PlayerElement, DateElement, SearchDates, SearchPlayers = 2):
        self.LocationName = LocationName
        self.CourseURL = CourseURL
        self.CourseNames = CourseNames
        self.SearchTimes = SearchTimes
        self.PlayerElement = PlayerElement
        self.DateElement = DateElement
        self.SearchDays = [int(i) for i in SearchDates.split(',')]
        self.SearchPlayerCount = [int(i) for i in SearchPlayers.split(',')] 
        self.FoundTimes = {}

    # Function to find the slots availble on the return value
    def __FindTimes(self, InputPage,aCourse=""):
        # Foreach time slot in RequiredTimes look for that text in the page, if found return the value
        results = []

        if aCourse == "" or aCourse == "*":
            ## Itterate over values for any course
            for aTimeSlot in self.SearchTimes:
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
                for aTimeSlot in self.SearchTimes:
                    # look for time slots
                    if (str(aTimeSlot) in li.text) and (aCourse in li.text):
                        # Time slot found!
                        results.append(aTimeSlot)

        ## Return found list
        return results
    
    # Function To load the page with target data
    def __LoadPage(self,PlayerCount,DateToSearch):
        try: 
            # Todo: Build Selinum bot to open page one then submit
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--window-size=1920x1080")
            chrome_options.add_argument("--incognito")
            chrome_options.add_argument("--no-sandbox")
            browser = webdriver.Chrome(options=chrome_options)

            #Load Page
            browser.get(self.CourseURL)
            time.sleep(1)

            #If redirected to /preSearch then hit submit
            currentURL = browser.current_url
            if currentURL.find("preSearch") != -1:
                # Get first bad refresh over
                time.sleep(1)
                btnSubmit = browser.find_element_by_xpath("//button[contains(@class,'btn')]")
                btnSubmit.click()
                time.sleep(2)

                # Set The Player Value
                PlayerPicker = Select(browser.find_element_by_id(self.PlayerElement))
                PlayerPicker.select_by_visible_text(str(PlayerCount))
                # Set The Date Values
                DatePicker = browser.find_element_by_id(self.DateElement)
                DatePicker.click()
                DatePicker.clear()
                DatePicker.send_keys(DateToSearch)
                DatePicker.send_keys(Keys.RETURN)

                btnSubmit = browser.find_element_by_xpath("//button[contains(@class,'btn')]")
                btnSubmit.click()
                time.sleep(2)
                return browser.page_source
            else:
                # Set The Player Value
                PlayerPicker = Select(browser.find_element_by_id(self.PlayerElement))
                PlayerPicker.select_by_visible_text(PlayerCount)
                # Set The Date
                DatePicker = browser.find_element_by_id(self.DateElement)
                DatePicker.clear()
                DatePicker.send_keys(DateToSearch)
                DatePicker.send_keys(Keys.RETURN)
                # Wait until data loaded
                time.sleep(1)
                return browser.page_source
            
        except:
            e = sys.exc_info()
            logging.error(f"Error Occured: {e}, PAGE; {self.CourseURL}, DATEELEMENT: {self.DateElement}, PLAYERELEMENT {self.PlayerElement}")
            return ""

    # Function To Get Next X day of the week
    def __GetNextDate(self,DayOfWeek):
        ## Input Values
        ## 0 Monday - 6 Sunday
        ## Output Values
        ## Date of next given DOW, formated 10/12/2020

        d = datetime.now()
        while d.weekday() != DayOfWeek:
            d = d + timedelta(days=1)

        # Return the format    
        return d.strftime('%m/%d/%Y')

    # Function to build a list of times
    def FindSpots(self):
        # Itterate over courses in the list
        for aCourse in self.CourseNames:
            tempset = []
            # Itterate over Days of the week to search
            for aDay in self.SearchDays:
                ## Variable for Next TargetDate
                NextDate = self.__GetNextDate(aDay)
                ## Itterate over player count
                for aPlayerCount in self.SearchPlayerCount:
                    ## Load the page and return the value
                    logging.info(f"Checking the site: {self.LocationName}. Looking for the following Tee Times {self.SearchTimes[0]} - {self.SearchTimes[-1]} on the date: {NextDate}, for {aCourse} course, for a count of {aPlayerCount} player(s).")
                    ReturnedPage = self.__LoadPage(DateToSearch=NextDate,PlayerCount=aPlayerCount)
                    tempset.append({"PlayerCount": aPlayerCount, "Date": NextDate, "Times": self.__FindTimes(InputPage=ReturnedPage)})
        
            # Consolodate results based on Course Name
            self.FoundTimes[aCourse] = tempset
        return True
    
    # Pretty Functions
    def __str__(self):
        return f"Name: {self.LocationName}, CourseURL: {self.CourseURL}, CourseNames: {self.CourseNames}, SearchTimes: {self.SearchTimes}, PlayerElement: {self.PlayerElement}, DateElement: {self.DateElement}, SearchDates: {self.SearchDays}, SearchPlayers: {self.SearchPlayerCount} "
    
    def __repr__(self):
        return f"golfcourse(Name={self.LocationName}, CourseURL={self.CourseURL}, CourseNames={self.CourseNames}, SearchTimes={self.SearchTimes}, PlayerElement={self.PlayerElement}, DateElement={self.DateElement}, SearchDates={self.SearchDays}, SearchPlayers={self.SearchPlayerCount} "
    