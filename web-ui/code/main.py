import requests
from flask import Flask, flash, redirect, render_template, request
import os

# App Config
app = Flask(__name__)

# DataStore value map
ValueMap = [{'players':'Options'},{'DaysOfWeek':'Options'},{'Numbers':'notificationTimes'},{'Enabled':'notificationTimes'},{'start':'notificationTimes'},{'end':'notificationTimes'},{'teeTimeStart':'searchTimes'},{'teeTimeEnd':'searchTimes'}]
    

# Function to save value to DataStore
def SaveValue(ValueName: str, ValueItem: str, DataStoreKind: str):
    pass

# Function to load values from DataStore
def GetValues():
    pass

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
    return render_template('edit.html')

#Main Function handler
@app.route("/", methods=['GET'])
def main():
    return render_template('index.html')

if __name__ == "__main__":
    ## Run APP
    app.run(host='0.0.0.0', port=8080)