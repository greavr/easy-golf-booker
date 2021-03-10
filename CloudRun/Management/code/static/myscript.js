function SaveValue(fieldname, newValue) {
    // Function to send backend API call to webhost to save values
}

function CheckChange(divID) {
    // Function to check if value has changed in the form and will call SaveValue with the field name and new value

    // Special use cases:
    // Day Of Week
    // Phone number, player count to be broken into array, comma seperated
}

function openCity(evt, cityName) {
    // Declare all variables
    var i, tabcontent, tablinks;
  
    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
  
    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
  
    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(cityName).style.display = "block";
    evt.currentTarget.className += " active";
  }

  function RefreshData(){
    fetch("https://golfbot-teetime-finder-4isbwvleta-uw.a.run.app")
    .then(function (response) {
      document.querySelector('#RefreshTimes').textContent = response.json();
    })
    .catch(function (error) {
      console.log("Error: " + error);
    });
  }