#This script will take a url and monitor it for changes. It will then create an event in MISP.
#It does this by pulling links with a specified TAG from MISP and querying it, creating a hash, and comparing it to a pre-existing hash. If there's a change, a MISP event will be created.
#You will need a text file with an empty dictionary titled MISP_Monitor_Website_options.txt for it to run.
#Written By: https://github.com/TRaven/
#Version: 5

import time, hashlib, re, uuid, os, json, requests
from urllib.request import urlopen, Request
from pymisp import PyMISP
from pymisp import MISPEvent

# The URL pointing to the MISP instance
misp_url= "[YOUR MISP URL]"
# The MISP API key
misp_key = "[YOUR MISP API KEY]"
# The Tag that will be pulled
misp_attribute_tag = "YOUR RELEVANT TAG"

def get_hash():
    print("GETTING THE HASH")
    # setting the URL you want to monitor
    url = Request(monitored_url, headers={'User-Agent':'Mozilla/5.0'})

    # Perform a GET request and load the content of the website and store it in a variable
    response = urlopen(url).read()

    # Create the hash
    the_hash = hashlib.sha224(response).hexdigest()
    return the_hash

def compare_hash(current_hash, new_hash):
    print("COMPARING")
    # check if new hash is same as the previous hash    
    if new_hash == current_hash: 
        print('SAMESIES')
    # if something changed in the hashes 
    else:
        # notify 
        print("SOMETHING CHANGED")
        monitored_url_dict[monitored_url][0] = new_hash
        misp_work()
        with open('MISP_Monitor_Website_options.txt','w') as file:
            file.write(json.dumps(monitored_url_dict))
        
def misp_work():
    # create MISP instance to interact with using Python methods
    misp = PyMISP(misp_url, misp_key, ssl=False, debug=False)
    # Start Populating the Event that's going to be generated.
    event = MISPEvent()
    # Set the distribution of the event to our sharing group
    event.distribution = 1
    # Populate the info that will be seen in the events page.
    event.info = subject + " updated."
    event.add_tag(misp_attribute_tag)
    # Add the link to the advisory page as an attribute to the Event.
    event.add_attribute('link', monitored_url)
    # Add the event with the info filled in above.
    event = misp.add_event(event, pythonify=True)
    # Publish the Event
    event = misp.publish(event.id, alert=False)  


if __name__ == '__main__':
    # First let's pull the 
    payload = {"type":"link", "tags":"BCST Monitored URL"}
    headers = {"Authorization" : misp_key, "Content-type" : "application/json"}
    response = requests.post(misp_url + "/attributes/restSearch", headers=headers, json=payload, verify=False)
    the_data = json.loads(response.text)["response"]["Attribute"]
    
    # Open the file that has a dictionary with our required data as readable
    with open('MISP_Monitor_Website_options.txt','r') as monitored_url_dict_file:
        monitored_url_dict = json.loads(monitored_url_dict_file.read())
        for i in the_data:
            monitored_url = i["value"]
            monitored_url_id = i["id"]
            # If the url already is in our text file, just pull 
            if monitored_url in monitored_url_dict:
                current_hash = monitored_url_dict[monitored_url][0]
                subject = monitored_url_dict[monitored_url][1]
            else:
                subject = i["comment"]
                current_hash = ""
                monitored_url_dict[monitored_url] = [current_hash, subject, 0]
    
            # find the current hash
            new_hash = get_hash()
            compare_hash(current_hash, new_hash)
