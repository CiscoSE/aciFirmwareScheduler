__license__ ='''Copyright (c) 2022 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.'''

import requests
import time, json, re

#Required for self signed certificate handling.
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class loggingFunctions:
    def __init__(self, silent=False):
        self.silent = silent
        return

    def writeEvent(self, msg, msgType='INFO'):
        # We call this so that if we want to write a log file in the future, we have that option.
        self.writeScreen(msg, msgType)
        return

    def writeLog(self):
        #If we add output to file later, this may get used. 
        return

    def writeScreen(self, msg, msgType='INFO'):
        if msgType == 'INFO':
            if self.silent == False:
                print(f"[ {textColors.INFO}INFO{textColors.noColor} ] {msg}")
        elif msgType == 'WARN':
            if self.silent == False:
                print(f"[ {textColors.WARN}WARN{textColors.noColor} ] {msg}")
        elif msgType == "FAIL":
            if self.silent == False:
                print(f"[ {textColors.FAIL}FAIL{textColors.noColor} ] {msg}")
            exit()
        else:
            if self.silent == False:
                print(f"[ {textColors.FAIL}UNKNOWN{textColors.noColor} ] {msg}")
                print(f"This is a developer bug. Script will exit")
            exit()
        return

class textColors:
        noColor = '\x1b[0m'
        INFO = '\033[32m'   # Green
        WARN = '\033[33m'   # Yellow
        FAIL = '\033[31m'   # Red

class timeFunctions:
    def __init__(self):
        return

    def getCurrentTime(self):
        return time.strftime("%Y%m%d%H%M%S")

class urlFunctions:
    def __init__(self, args):
        self.debug = args.debug
        self.apicUser = args.apicUser
        self.password = args.password
        self.apicName = args.apicName
        self.domain = args.domain
        if self.debug >= 4:
            self.silent = False
        else:
            self.silent = args.silent
        return

    def getData(self, url, data='', headers={"Content-Type": "Application/json"},requestType='post', cookie='' ):
        if self.debug >= 1:
            loggingFunctions(self.silent).writeEvent(msg=f"URL:\t\t{url}", msgType='INFO')
            loggingFunctions(self.silent).writeEvent(msg=f"Data:\t\t{data}".replace(self.password,"REMOVED_PASSWORD"),msgType='INFO')
            loggingFunctions(self.silent).writeEvent(msg=f"Headers:\t{headers}",msgType='INFO')
            loggingFunctions(self.silent).writeEvent(msg=f"request Type:\t{requestType}", msgType='INFO')
        if requestType == 'post':
            # This is for making changes. 
            if self.debug >= 2:
                loggingFunctions(self.silent).writeEvent(msg=f"Starting post call to APIC", msgType='INFO')
            try:
                # Our attempt post changes to the API
                request = requests.post(url, data=data, headers=headers, timeout=10, cookies=cookie, verify=False)
            except:
                # This will terminate the script because our call was not successful.
                loggingFunctions(self.silent).writeEvent(msg=f"Unable to access {self.apicName}",msgType='FAIL')
        elif requestType == 'get':
            # Used when we only want to read data from the API
            if self.debug >= 2:
                loggingFunctions(self.silent).writeEvent(msg=f"Starting get call to APIC", msgType='INFO')
            try:
                # Our attempt to read data from the API
                request = requests.get(url, headers=headers, verify=False, timeout=10, cookies=cookie)
            except:
                # This will terminate the script because our call was not successful.
                loggingFunctions(self.silent).writeEvent(msg=f"Unable to access {self.apicName}",msgType='FAIL') 
        if re.match("20[0-9]", f"{request.status_code}"):
            # We are looking for a 200 result that tells us were were successful in accessing the API
            if self.debug >= 1:
                loggingFunctions(self.silent).writeEvent(msg="Request was successful", msgType='INFO')
            return request.text
        else:
            # Output if we received something other than a 20x return code. 
            loggingFunctions(self.silent).writeEvent(msg='Failed to access APIC API', msgType='WARN')
            loggingFunctions(self.silent).writeEvent(msg=f'Reason: {request.reason}', msgType='WARN')
            if self.debug >= 1:
                loggingFunctions(self.silent).writeEvent(msg=request.text, msgType='FAIL')
            exit()

    def getCookie(self):
        # Handling Domain support.
        if self.domain != '':
            # We have a domain name, so we are formating the request differently.
            name_pwd = {'aaaUser':{'attributes': {'name': f'apic:{self.domain}\\{self.apicUser}', 'pwd': f"{self.password}"}}}
        else:
            #If there is no domain, we format the JSON without the domain structure. 
            name_pwd = {'aaaUser':{'attributes': {'name': self.apicUser, 'pwd': f"{self.password}"}}}
        # Making sure we have the right JSON format. 
        json_credentials = json.dumps(name_pwd)
        # Calling getData to access the API.
        logonRequest = self.getData(url=f"https://{self.apicName}/api/aaaLogin.json", data=json_credentials, headers={"Content-Type": "application/json"})
        if self.debug > 1:
            loggingFunctions(self.silent).writeEvent(msg=f'Logon Request Response:\n{logonRequest}')
        logonRequestAttributes = json.loads(logonRequest)['imdata'][0]['aaaLogin']['attributes']
        if self.debug > 2:
            loggingFunctions(self.silent).writeEvent(msg=f'Logon Request Attributes\n{logonRequestAttributes}', msgType='INFO')
        # We only return the token, so it is important to reformat that into a cookie later if we want to use it.
        return {'APIC-Cookie': logonRequestAttributes['token']}

class inputSupport:
    def __init__(self):
        return

    def answerYesNo(self, message):
        questionExit = True
        while questionExit == True:
            #os.system('clear')
            print (f"{message}\n[Yes / No]")
            newServerName = input().lower()
            if newServerName in {'yes','y','ye'}:
                return True
            elif newServerName in {'no','n'}:
                return False