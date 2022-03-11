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

from re import I
from common import urlFunctions
from common import loggingFunctions as LOG
from common import inputSupport as DECISION
from datetime import timedelta as TIMEDELTA
import json, time, signal, sys

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
        if self.debug >= 1:
            LOG().writeEvent(msg='The following groups have been provided as groups to upgrade:',msgType='INFO')
            for group in self.args.firmwareGroups:
                LOG().writeEvent(msg=f'\t{group}',msgType='INFO')

        if self.debug >= 2:
            LOG().writeEvent(msg='Starting Group Verify function', msgType='INFO')
        status = 'UNKNOWN'
        aciGroupListResult = self.getListOfGroups()
        if self.args.firmwareGroups:            
            #See if we match any groups that should be upgraded.
            return self.compareGroups(aciGroups=aciGroupListResult, firmwareGroups=self.args.firmwareGroups)
        else:
            #If a group was not provided, list the groups that can be selected and bail out.
            self.bailOutOnSelection(aciGroupListResult)
        # We really should never get to this line, and if we do something is wrong.    
        LOG().writeEvent(msg="Something unexpected happened while assessing groups that we didn't account for.", msgType='FAIL')

    def bailOutOnSelection(self, aciGroups):
        LOG().writeEvent(msg='To use this script you must specify one of the following groups to be upgraded',msgType='WARN')
        for group in aciGroups:
            if self.debug >= 3:
                LOG().writeEvent(msg=f'Firmware Attribute Information:\n{group}',msgType='INFO')
            for key, value in group['firmwareFwGrp']['attributes'].items():
                if key == 'name':
                    LOG().writeEvent(msg=f'\t{value}', msgType='WARN')
        LOG().writeEvent(msg="Thats all folks!!!", msgType='FAIL')
        exit()

    def compareGroups(self, aciGroups, firmwareGroups):
        returnList={}
        if self.debug >= 2:
            LOG().writeEvent(msg='Starting Group Comparison', msgType='INFO')
        if self.debug >= 3:
            LOG().writeEvent(msg=f'JSON we have to work with at this point:\n{aciGroups}', msgType='INFO')
            LOG().writeEvent(msg=f'Groups we know about:\n{firmwareGroups}', msgType='INFO')
        for group in aciGroups:
            groupName = group['firmwareFwGrp']['attributes']['name']
            if self.debug >= 1:
                LOG().writeEvent(msg=f'Assessing Group: {groupName}',msgType='INFO')
            if self.debug >= 3:
                LOG().writeEvent(msg=f'Firmware Attribute Information:\n{group}',msgType='INFO')
            if groupName in firmwareGroups:
                LOG().writeEvent(msg=f'Adding {groupName} to list of groups to upgrade',msgType='INFO')
                returnList[(groupName)] = group['firmwareFwGrp']['attributes']['dn']
        if self.debug >= 1:
            LOG().writeEvent(f'Number of matching groups found:\t{len(returnList)}', msgType='INFO')
        if self.debug >= 3:
            LOG().writeEvent(f'List of groups we are returning for uprade:\n{returnList}', msgType='INFO')
        if not len(returnList) > 0:
            self.bailOutOnSelection(aciGroups)
        else:
            return returnList

    def getListOfGroups(self):
        #Where we find groups
        requestPath=f'https://{self.args.apicName}/api/node/class/firmwareFwGrp.json?&order-by=firmwareFwGrp.modTs|desc'
        #Call getData to get list of groups. 
        jsonResponseRAW = urlFunctions(self.args).getData(url=f'{requestPath}',requestType='get',cookie=self.cookie)
        if self.debug >= 3:
            LOG().writeEvent(f'JSON Response \n{jsonResponseRAW}')
        
        # If we got nothing back (totalcount = 0), we need to do something about that.
        aciTotalCount = json.loads(jsonResponseRAW)['totalCount']
        if self.debug >= 1:
            LOG().writeEvent(f'Number of Groups found in ACI:\t{aciTotalCount}')

        aciGroups = json.loads(jsonResponseRAW)['imdata']
        if self.debug >= 3:
            LOG().writeEvent(f'Groups in JSON Format:\n{aciGroups}')
        if not int(aciTotalCount) > 0:
            LOG().writeEvent(msg=f'No groups were found in ACI. This script cannot schedule firmware updates', msgType='WARN')
            LOG().writeEvent(msg=f'Create groups in ACI before running this script again', msgType='FAIL')
            exit()
        else:
            return aciGroups

class phase3:
    def __init__(self):
        return

    def confirmTimeToStart(self, minutesUntilStart):
        signal.signal(signal.SIGINT, lambda x, y: sys.exit(0))
        currentTime= time.time() 
        startTime = currentTime + (minutesUntilStart * 60)
        if DECISION().answerYesNo(
            message=f'Firmware is scheduled to run at {time.ctime(startTime)}\nCurrent Local Time is: {time.ctime(currentTime)}'
            ) == True:
            while True:
                time.sleep(1)
                if time.time() > startTime:
                    break
                timeDifference = startTime - time.time() 
                print(f"Count Down Timer: {TIMEDELTA(seconds=int(timeDifference))}",end='....\r',flush=True)
        else:
            LOG().writeEvent(msg="Exiting without upgrading", msgType='FAIL')
            exit()
        return

