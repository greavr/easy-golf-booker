from bs4 import BeautifulSoup
from datetime import datetime, timedelta

## Application Variables
targetPage = ("https://hardingpark.ezlinksgolf.com/index.html#/search")
targetDate = ""
RequiredTimes = ["9:15 AM", "9:30 AM", "9:45 AM"]

## Application logic
# Load Page
# Look for time values required
# If found send TXT message
# If not found die

def Notify(FoundRange):
    # Todo
    pass

def FindTimes(InputPage):
    # Foreach time slot in RequiredTimes look for that text in the page, if found return the value
    result = []
    ## Itterate over values
    for aTimeSlot in RequiredTimes:
        # look for time slots
        if InputPage.find(aTimeSlot):
            # Time slot found!
            result.append[aTimeSlot]

    ## Return found list
    return result


def LoadPage():
    return BeautifulSoup(targetPage + targetDate)

def Main():
    # Controller
    ## Load Page
    PageData = LoadPage()
    FoundTimeSlots = FindTimes(PageData)
    ## Check if any found
    if len(FoundTimeSlots) > 0:
        print (f"Found times {FoundTimeSlots}")
        Notify(FoundTimeSlots)
    
    ## Else do nothing


if __name__ == "__main__":
    Main("")