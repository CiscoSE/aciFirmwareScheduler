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

from common import urlFunctions
from common import loggingFunctions as LOG
import json

class phase1:
    def __init__(self, args):
        self.debug = args.debug
        self.args = args
        return
    
    def getCookie(self):
        URL = urlFunctions(args=self.args)
        cookie = URL.getCookie()
        if cookie:
            if self.args.debug:
                # We only print the cookie if we are in debug mode
                print(f"Cookie:\n{cookie}")
            # We print status either way.    
            LOG().writeEvent(msg='Cookie Obtained', msgType="INFO")
        else:
            LOG().writeEvent(msg='Cookie was not obtained', msgType='FAIL')
            exit()
        return cookie


class phase2:
    #check of group requested exist and remediate if necessary. 
    def __init__(self, cookie, args):
        self.cookie = cookie
        self.debug = args.debug
        self.args = args
        return
    
    def verifyGroups(self):
        if self.debug >=3:
            LOG().writeEvent(msg='Starting Group Verify function', msgType='INFO')
        status = 'UNKNOWN'
        self.getListOfGroups()
        return status
    
    def getListOfGroups(self):

        #Where we find groups
        requestPath=f'https://{self.args.apicName}/api/node/class/firmwareFwGrp.json?&order-by=firmwareFwGrp.modTs|desc'
        #Call getData to get list of groups. 
        jsonResponse = urlFunctions(self.args).getData(url=f'{requestPath}',requestType='get',cookie=self.cookie)
        print(self.debug)
        if self.debug:
            LOG().writeEvent(f'JSON Response \n{jsonResponse}')
        return