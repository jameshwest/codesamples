#www.tide-forecast.com Web Crawler

## History
   * Feb 2012 Implemented as a coding exercise.  The current implementation shows
     data for four locations:  
......* Half Moon Bay, California
......* Huntington Beach, California
......* Providence, Rhode Island
......* Wrightsville Beach, North Carolina
   
## How to Run
   This program depends on Python 2.7 which must be present on the system on which it runs

   Usage:  showlowtides [-xml]
      -xml :  prints data in as XML (without DTD or schema)
              Without this switch, data is printed as an UTF-8 formatted table

   It prints the low times of 4 geographic locations that occur after sunrise and before sunset and
   the hight of the tide in feet and meters.  Heights can be positive or negative numbers
   The lower the number, the lower the tide

   Output:
      Location | Date | Time | height meters | height feet

## Implementation Details
   This prgram scapes HTML data the site https://www.tide-forecast.com.  Each location
   is identified by a unique URL.  The basic Algorithm is as follows
     
      for each location
         create the URL for the location
         Fetch the data
         Parse the HTML
         Cache the parsed HTML data into unique tidalEvents (defined below)
         Filter the Data
         Sort the remaining Data (sorted by time)
         Print the sorted Data


### Information Model

    Each Page HAS-A
         location          :  A string, such as "Providene, Rhode Island"
         url               :  A string, an example https://www.tide-forecast.com/locations/Providence-Rhode-Island/tides/latest
         list of dateEntry :  A complex structure

    Each dateEntry HAS-A
         dayStamp          : A string, The day for the data contained in this entry
         sunRiseTime
         sunSetTime
         One or Two lowTideEntry's :  A complex structure.  Most days have two low tides, some days only have one

    Each lowTideEntry HAS-A
         timestamp         : A date/time stamp representing when the low tide will occur
         heightMeters      : A floating point number, representing the tide hight in meters
         heightFeet        : A floating point number, representing the tide hight in meters
    
### Raw Data Notes
   * At the time of writing, the site only returned data in HTML.  Requests for data as JSON or XML returned errors
   * Parsing the data is a little bit of a challenge because the "date" field in the HTML uses the rowspan construct
     so date is not in ever table row

### Language Choice
   Implementated in Python.  Predict that this choice will provide a robust implementation that others can understand
   that can be written in the least amount of time

### How tested
   Enumerate the different options

      showlowtides 

      showlowtides -xml

   Compare the data provided with the data on the source web pages.
   Check for completeness, data accuracy and correct order
