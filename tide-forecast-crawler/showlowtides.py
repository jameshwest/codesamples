#!/usr/bin/python 
from HTMLParser import HTMLParser # See https://docs.python.org/2/library/htmlparser.html 
import httplib 
import sys
import traceback
import datetime

###  Times come back as string.  HH:MM [AM|PM] TimeZone.  In order to compare times,
###  we need to convert them to a numeric value to compare. 
def timeToNumeric(timeAsString):
   timeVal = 0
   if (timeAsString != None):
      splitTime = timeAsString.strip(" \t").split(" ")
      hour,minute = splitTime[0].split(":")
      hour = int(hour)
      minute = int(minute)
      amOrPm = splitTime[1].strip(" \t\r\n")
      if (amOrPm == "PM"):
         hour = + 12
      timeVal = (hour * 60) + minute
   return timeVal

###  Date come back as string.  <Day of Week> <Date of Month> <Month Name>
###  we need to convert them to a numeric value to compare.
###  NOTE WELL:  We add dateNumberics and timeNumerics together to create a sort key
def dateToNumeric(dateAsString):
   #Friday 16 February
   dayName,dayNum,month = dateAsString.strip("\n\r\t ").split(" ")
   # Ignore the dayName
   month = month.lower()
   monthNum = -1
   if (month.startswith("jan")):
      monthNum = 1
   elif (month.startswith("feb")):
      monthNum = 2
   elif (month.startswith("mar")):
      monthNum = 3
   elif (month.startswith("apr")):
      monthNum = 4
   elif (month.startswith("may")):
      monthNum = 5
   elif (month.startswith("jun")):
      monthNum = 6
   elif (month.startswith("jul")):
      monthNum = 7
   elif (month.startswith("aug")):
      monthNum = 8
   elif (month.startswith("sep")):
      monthNum = 9
   elif (month.startswith("oct")):
      monthNum = 10
   elif (month.startswith("nov")):
      monthNum = 11
   elif (month.startswith("dec")):
      monthNum = 12
   dateNum = (monthNum * 100 + int(dayNum)) * 10000
   return dateNum
   


def checkTide(tideDef, timeSunRise, timeSunSet):
   sunRiseNum    = timeToNumeric(timeSunRise)
   sunSetNum     = timeToNumeric(timeSunSet)
   tideTimeNum   = timeToNumeric(tideDef.timeStamp)
   # We want the time to be AFTER sunRise
   inBounds = True
   if (tideTimeNum < sunRiseNum):
      inBounds = False
   if (tideTimeNum > sunSetNum):
      inBounds = False
   return inBounds

###############################    Major class that does most the work  ########################################

class TideEntry(object):
   def __init__(self, location, timestamp, timezone, daystamp, level, levelmetric):
      self.location    = location
      self.timeStamp   = timestamp
      self.timeZone    = timezone
      self.daystamp    = daystamp
      self.level       = level
      # Earlier processing stripped the unit off the 'feet' datum.  String the trailing 'm' off the metric datum
      # and sometimes it has a trailing 'meters' ... so much for consistency :-)
      self.levelMetric = levelmetric.strip(" meters")

   def __str__(self):
      return "TIDE -%s %s %s %s %s %s" % (self.location, self.timeStamp, self.timeZone, self.daystamp, self.level, self.levelMetric)

class DataEntry(object):
   def __init__(self, dayStamp):
      self.dayStamp = dayStamp
      self.timeZone = None
      self.sunRise  = None
      self.sunSet   = None
      self.lowTides = []
   
   def __str__(self):
      return "ENTRY -%s %s %s %s" % (self.dayStamp, self.timeZone, self.sunRise, self.sunSet)

   def addTimeZone(self, timezone):
      self.timeZone = timezone

   def addSunRise(self, timestamp):
      self.sunRise = timestamp

   def addSunSet(self, timestamp):
      self.sunSet = timestamp

   def addLowTide(self, tide):
      self.lowTides.append(tide)

class DataEntry(object):
   def __init__(self, dayStamp):
      self.dayStamp = dayStamp
      self.timeZone = None
      self.sunRise  = None
      self.sunSet   = None
      self.lowTides = []
   
   def addTimeZone(self, timezone):
      self.timeZone = timezone

   def addSunRise(self, timestamp):
      self.sunRise = timestamp

   def addSunSet(self, timestamp):
      self.sunSet = timestamp

   def addLowTide(self, tide):
      self.lowTides.append(tide)

class MyTidalPage(HTMLParser):
   def fetchData(self, locName):
      wasSuccess = False
      self.locationName = locName
      self.uri = "/locations/%s/tides/latest" % locName
      httpConnection = None
      try:
         httpConnection = httplib.HTTPSConnection('www.tide-forecast.com')
         httpConnection.request("GET", self.uri)
         httpRsp        = httpConnection.getresponse()
         if (httpRsp.status != 200):
            print("Http request to %s failed with status code = %s" % (self.uri, httpRsp.status))
         self.data = httpRsp.read()
         # HACK:  The tide level in feet is wrapped with <span> tags ... nothing else is.  Remove that construct
         #        This makes the parsing below more uniform
         self.data = self.data.replace('<td class="level">(<span class="imperial">', '<td class="level">').replace(' feet</span>)</td>', "</td>")
         wasSuccess = True
      except:
         excType, excValue, excTraceback = sys.exc_info()
         ex = traceback.format_exception(excType, excValue, excTraceback)
         print("Http data retrieval failed with exception")
         print(ex)
      finally:
         if (httpConnection != None):
            httpConnection.close()
      return wasSuccess

   def parseData(self, locName):
      # Initialize the attributes that keep track of data parsing
      self.locName         = locName
      self.currentTag      = None
      self.state           = None
      self.currentData     = None
      self.dataEvent       = None
      self.dataDate        = None
      self.dataTime        = None
      self.dataTZ          = None
      self.dataLevelFeet   = None
      self.dataLevelMetric = None
      self.day2Data        = {}
      # Assume we'll be successful ... change if we fail
      wasSuccess           = True
      try:
         self.feed(self.data)
      except:
         excType, excValue, excTraceback = sys.exc_info()
         ex = traceback.format_exception(excType, excValue, excTraceback)
         print("HTML data parsing failed with exception")
         print(ex)
         wasSuccess = False
      return wasSuccess

   ##  HTML Parsing Section
   ##  We skip all tage until we hit an h2 tag with the data '*Tide table:'
   def handle_starttag(self, tag, attrs): 
      self.currentTag = tag
      if (self.state == "SEEN_H2_TIDE_TABLE"):
         if (tag == "table"):
            self.state = "SEEN_START_OF_TABLE"
      elif (self.state == "SEEN_START_OF_TABLE"):
         if (tag == "td"):
            ## Now we can parse the data.  <td> with no attributes is the event type
            ## Events we are interested in are "Sunrise", "Sunset", and "Low Tide".  In the future maybe we'll care about "High Tide"
            if (len(attrs) == 0 or attrs[0][1] == "tide"):
               self.currentData = "EVENT"
            else :
               # Otherwise, we determine the data time by paring the value of the 'class' attribute
               self.currentData = attrs[0][1]

   def filterSortPrint(self):
      self.filteredTides = {}
      for entry in self.day2Data.values():
         dateNumeric = dateToNumeric(entry.dayStamp)
         sunRise = entry.sunRise
         sunSet  = entry.sunSet
         firstTide = entry.lowTides[0]
         timeFirstTide = timeToNumeric(firstTide.timeStamp)
         inBounds = checkTide(firstTide, sunRise, sunSet)
         if (inBounds == True):
            # Make a unique time identifier.  Add the tide time to the dateNumeric
            sortKey = dateNumeric + timeFirstTide;
            self.filteredTides[sortKey] = firstTide
         if (len(entry.lowTides) >= 2):
            secondTide = entry.lowTides[1]
            timeSecondTide = timeToNumeric(secondTide.timeStamp)
            inBounds = checkTide(secondTide, sunRise, sunSet)
            if (inBounds == True):
               sortKey = dateNumeric + timeSecondTide;
               self.filteredTides[sortKey] = secondTide
      keyList = self.filteredTides.keys()
      keyList.sort()

      for key in keyList:
         tide = self.filteredTides[key]
         print("%35s | %22s | %10s | %s | %s feet/%s meters" % (tide.location, tide.daystamp, tide.timeStamp, tide.timeZone, tide.level, tide.levelMetric))
     

   def handle_endtag(self, tag): 
      if (self.state == "SEEN_START_OF_TABLE"):
         if (tag == "tr"):
            # This indicates the end of a data item.  
            # Make an entry
            currentDataEntry = None
            if (self.day2Data.has_key(self.dataDate) == False):
               currentDataEntry = DataEntry(self.dataDate)
               self.day2Data[self.dataDate] = currentDataEntry
            else:
               currentDataEntry = self.day2Data[self.dataDate]

            ## Events we are interested in are "Sunrise", "Sunset", and "Low Tide".  In the future maybe we'll care about "High Tide"
            if (self.dataEvent == "Sunrise"):
               currentDataEntry.addSunRise(self.dataTime)
               currentDataEntry.addTimeZone(self.dataTZ) # NOTE:  Assume that all times are in the same TZ
            elif (self.dataEvent == "Sunset"):
               currentDataEntry.addSunSet(self.dataTime)
               currentDataEntry.addTimeZone(self.dataTZ) # NOTE:  Assume that all times are in the same TZ
            elif (self.dataEvent == "Low Tide"):
               tideEntry = TideEntry(self.locName, self.dataTime, self.dataTZ, self.dataDate, self.dataLevelFeet, self.dataLevelMetric)
               currentDataEntry.addLowTide(tideEntry)
               #print (tideEntry)
         elif (self.state == "SEEN_START_OF_TABLE" and tag == "table"):
            # We've hit the end of the table
            self.state = None

   def handle_data(self, data): 
      mydata = data.strip("\n\r\t ")
      if (self.currentTag == 'h2' and self.state == None):
         if (mydata.endswith("Tide table:")):
            self.state = "SEEN_H2_TIDE_TABLE"
      elif (self.state == "SEEN_START_OF_TABLE"):
         if (self.currentData == "EVENT"):
            self.dataEvent = mydata
         elif (self.currentData == "date"):
            self.dataDate = mydata
         elif (self.currentData == "time" or self.currentData == "time tide"):
            self.dataTime = mydata
         elif (self.currentData == "time-zone"):
            self.dataTZ = mydata
         elif (self.currentData == "level"):
            ## Level is contained within a <span>.  We need to parse that
            self.dataLevelFeet = mydata
         elif (self.currentData == "level metric"):
            self.dataLevelMetric = mydata
         self.currentData = None
      

locations = ['Providence-Rhode-Island', 'Wrightsville-Beach-North-Carolina', 'Half-Moon-Bay-California', 'Huntington-Beach']
#locations = ['Providence-Rhode-Island']
#######################    MAIN   #######################################3
def main():
   if (len(sys.argv) != 1):
      print ("Usage: %s [-xml]" % sys.argv[0])
      print ("\n Prints lowtide data for 4 geographic locations")
      sys.exit(1)

   ## At this point, we've check the inputs.  Now attempt to get the data
   for locationName in locations:
      tidePage = MyTidalPage()
      result = tidePage.fetchData(locationName)
      if (result == True):
         result = tidePage.parseData(locationName)
      if (result == True):
         tidePage.filterSortPrint()

if __name__ == "__main__":
   main()
