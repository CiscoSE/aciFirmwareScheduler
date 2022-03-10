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
import time
import json
import re

#Required for self signed certificate handling.
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class loggingFunctions:
    def __init__(self):
        return

    def writeEvent(self, msg, msgType='INFO'):
        self.writeScreen(msg, msgType)
        return

    def writeLog(self):
        #If we add output to file later, this may get used. 
        return

    def writeScreen(self, msg, msgType='INFO'):
        if msgType == 'INFO':
            print(f"[ {textColors.INFO}INFO{textColors.noColor} ] {msg}")
        elif msgType == 'WARN':
            print(f"[ {textColors.WARN}WARN{textColors.noColor} ] {msg}")
        elif msgType == "FAIL":
            print(f"[ {textColors.FAIL}FAIL{textColors.noColor} ] {msg}")
            exit()
        else:
            print(f"[ {textColors.FAIL}UNKNOWN{textColors.noColor} ] {msg}")
            print(f"This is a developer bug. Script will exit")
            exit()
        return

class textColors:
        noColor = '\x1b[0m'
        INFO = '\033[32m'
        WARN = '\033[33m'
        FAIL = '\033[31m'

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
        return

    def getData(self, url, data='', headers={"Content-Type": "Application/json"},requestType='post', cookie='' ):
        if self.debug == True:
            loggingFunctions().writeEvent(msg=f"URL:\t\t{url}", msgType='INFO')
            loggingFunctions().writeEvent(msg=f"Data:\t\t{data}".replace(self.password,"REMOVED_PASSWORD"),msgType='INFO')
            loggingFunctions().writeEvent(msg=f"Headers:\t{headers}",msgType='INFO')
            loggingFunctions().writeEvent(msg=f"request Type:\t{requestType}", msgType='INFO')
        if requestType == 'post':
            try:
                request = requests.post(url, data=data, headers=headers, timeout=10, cookies=cookie, verify=False)
            except:
               loggingFunctions().writeEvent(msg=f"Unable to access {self.apicName}",msgType='FAIL')
        elif requestType == 'get':
            try:
                request = requests.get(url, headers=headers, verify=False, timeout=10, cookies=cookie)
            except:
                loggingFunctions().writeEvent(msg=f"Unable to access {self.apicName}",msgType='FAIL') 
        if re.match("20[0-9]", f"{request.status_code}"):
            if self.debug == True:
                loggingFunctions().writeEvent(msg="Request was successful", msgType='INFO')
            return request.text
        else:
            loggingFunctions().writeEvent(msg='Failed to access APIC API', msgType='WARN')
            loggingFunctions().writeEvent(msg=f'Reason: {request.reason}', msgType='WARN')
            if self.debug == True:
                loggingFunctions().writeEvent(msg=request.text, msgType='FAIL')
            exit()

    def getCookie(self):
        name_pwd = {'aaaUser':{'attributes': {'name': self.apicUser, 'pwd': f"{self.password}"}}}
        json_credentials = json.dumps(name_pwd)
        logonRequest = self.getData(url=f"https://{self.apicName}/api/aaaLogin.json", data=json_credentials, headers={"Content-Type": "application/json"})
        logonRequestAttributes = json.loads(logonRequest)['imdata'][0]['aaaLogin']['attributes']
        return logonRequestAttributes['token']