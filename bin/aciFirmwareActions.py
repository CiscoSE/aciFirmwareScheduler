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
from sre_constants import GROUPREF_EXISTS
from common import urlFunctions
from common import loggingFunctions as LOG
from common import inputSupport as DECISION
from datetime import timedelta as TIMEDELTA
import json, time, signal, sys

class phase1:
    def __init__(self, args):
        self.debug = args.debug
        self.args = args
        if self.debug >= 4:
            self.silent = False
        else:
            self.silent = args.silent
        return
    
    def getCookie(self):
        URL = urlFunctions(args=self.args)
        cookie = URL.getCookie()
        if cookie:
            if self.args.debug >=2:
                # We only print the cookie if we are in debug mode
                print(f"Cookie:\n{cookie}")
            # We print status either way.    
            LOG(self.silent).writeEvent(msg='Cookie Obtained', msgType="INFO")
        else:
            LOG(self.silent).writeEvent(msg='Cookie was not obtained', msgType='FAIL')
            exit()
        return cookie


class phase2a:
    #check if groups requested exist and remediate if necessary. 
    def __init__(self, cookie, args):
        self.cookie = cookie
        self.debug = args.debug
        self.args = args
        if self.debug >= 4:
            self.silent = False
        else:
            self.silent = args.silent
        return
    
    def verifyGroups(self):
        if self.debug >= 1:
            LOG(self.silent).writeEvent(msg='The following groups have been provided as groups to upgrade:',msgType='INFO')
            for group in self.args.firmwareGroups:
                LOG(self.silent).writeEvent(msg=f'\t{group}',msgType='INFO')

        if self.debug >= 2:
            LOG(self.silent).writeEvent(msg='Starting Group Verify function', msgType='INFO')
        aciGroupListResult = self.getListOfGroups()
        if self.args.firmwareGroups:            
            #See if we match any groups that should be upgraded.
            return self.compareGroups(aciGroups=aciGroupListResult, firmwareGroups=self.args.firmwareGroups)
        else:
            #If a group was not provided, list the groups that can be selected and bail out.
            self.bailOutOnNoGroups(aciGroupListResult)
        # We really should never get to this line, and if we do something is wrong.    
        LOG(self.silent).writeEvent(msg="Something unexpected happened while assessing groups that we didn't account for.", msgType='FAIL')

    def bailOutOnNoGroups(self, aciGroups):
        LOG(self.silent).writeEvent(msg='To use this script you must specify one of the following groups to be upgraded',msgType='WARN')
        for group in aciGroups:
            if self.debug >= 3:
                LOG(self.silent).writeEvent(msg=f'Firmware Attribute Information:\n{group}',msgType='INFO')
            for key, value in group['firmwareFwGrp']['attributes'].items():
                if key == 'name':
                    LOG(self.silent).writeEvent(msg=f'\t{value}', msgType='WARN')
        LOG(self.silent).writeEvent(msg="Thats all folks!!!", msgType='FAIL')
        exit()

    def compareGroups(self, aciGroups, firmwareGroups):
        returnList={}
        if self.debug >= 2:
            LOG(self.silent).writeEvent(msg='Starting Group Comparison', msgType='INFO')
        if self.debug >= 3:
            LOG(self.silent).writeEvent(msg=f'JSON we have to work with at this point:\n{aciGroups}', msgType='INFO')
            LOG(self.silent).writeEvent(msg=f'Groups we know about:\n{firmwareGroups}', msgType='INFO')
        for group in aciGroups:
            groupName = group['firmwareFwGrp']['attributes']['name']
            if self.debug >= 1:
                LOG(self.silent).writeEvent(msg=f'Assessing Group: {groupName}',msgType='INFO')
            if self.debug >= 3:
                LOG(self.silent).writeEvent(msg=f'Firmware Attribute Information:\n{group}',msgType='INFO')
            if groupName in firmwareGroups:
                LOG(self.silent).writeEvent(msg=f'Adding {groupName} to list of groups to upgrade',msgType='INFO')
                returnList[(groupName)] = group['firmwareFwGrp']['attributes']['dn']
        if self.debug >= 1:
            LOG(self.silent).writeEvent(f'Number of matching groups found:\t{len(returnList)}', msgType='INFO')
        if self.debug >= 3:
            LOG(self.silent).writeEvent(f'List of groups we are returning for uprade:\n{returnList}', msgType='INFO')
        if not len(returnList) > 0:
            self.bailOutOnNoGroups(aciGroups)
        else:
            return returnList

    def getListOfGroups(self):
        #Where we find groups
        requestPath=f'https://{self.args.apicName}/api/node/class/firmwareFwGrp.json?&order-by=firmwareFwGrp.modTs|desc'
        #Call getData to get list of groups. 
        jsonResponseRAW = urlFunctions(self.args).getData(url=f'{requestPath}',requestType='get',cookie=self.cookie)
        if self.debug >= 3:
            LOG(self.silent).writeEvent(f'JSON Response \n{jsonResponseRAW}')
        
        # If we got nothing back (totalcount = 0), we need to do something about that.
        aciGroupsTotalCount = json.loads(jsonResponseRAW)['totalCount']
        if self.debug >= 1:
            LOG(self.silent).writeEvent(f'Number of Groups found in ACI:\t{aciGroupsTotalCount}')

        aciGroups = json.loads(jsonResponseRAW)['imdata']
        if self.debug >= 3:
            LOG(self.silent).writeEvent(f'Groups in JSON Format:\n{aciGroups}')
        if not int(aciGroupsTotalCount) > 0:
            LOG(self.silent).writeEvent(msg=f'No groups were found in ACI. This script cannot schedule firmware updates', msgType='WARN')
            LOG(self.silent).writeEvent(msg=f'Create groups in ACI before running this script again', msgType='FAIL')
            exit()
        else:
            return aciGroups

class phase2b:
    #check if firmware requested exists and remediate if necessary.
    def __init__(self, cookie, args):
        self.cookie = cookie
        self.debug = args.debug
        self.args = args
        if self.debug >= 4:
            self.silent = False
        else:
            self.silent = args.silent
        return

    def verifyFirmware(self):
        aciFirmwareList = self.getListOfFirmware()
        if self.args.firmwareVersion:
            if self.debug >= 1:
                LOG(self.silent).writeEvent(msg=f'Checking that firmware version {self.args.firmwareVersion} is available',msgType='INFO')
            return self.compareFirmware(aciFirmwareList=aciFirmwareList, firmwareVersion=self.args.firmwareVersion)
        else:
            #No group was provided, so we will provide a list of options back to the console. 
            self.bailOutOnNoFirmware(aciFirmwareList)
        return

    def getListOfFirmware(self):
        #Where we find firmware
        requestPath=f'https://{self.args.apicName}/api/node/class/firmwareFirmware.json?&order-by=firmwareFirmware.modTs|desc&query-target-filter=eq(firmwareFirmware.type,"switch"'
        #Call getData to get list of firmware. 
        jsonResponseRAW = urlFunctions(self.args).getData(url=f'{requestPath}',requestType='get',cookie=self.cookie)
        if self.debug >= 3:
            LOG(self.silent).writeEvent(f'JSON Response \n{jsonResponseRAW}')
        
        # If we got nothing back (totalcount = 0), we need to do something about that.
        aciFirmwareTotalCount = json.loads(jsonResponseRAW)['totalCount']
        if self.debug >= 1:
            LOG(self.silent).writeEvent(f'Number of firmware found in ACI:\t{aciFirmwareTotalCount}')

        aciFirmware = json.loads(jsonResponseRAW)['imdata']
        if self.debug >= 3:
            LOG(self.silent).writeEvent(f'Groups in JSON Format:\n{aciFirmware}')
        if not int(aciFirmwareTotalCount) > 0:
            LOG(self.silent).writeEvent(msg=f'No Firmware were found in ACI. This script cannot schedule firmware updates', msgType='WARN')
            LOG(self.silent).writeEvent(msg=f'Import firmware for your switches into ACI before running this script again', msgType='FAIL')
            exit()
        else:
            return aciFirmware

    def compareFirmware(self, aciFirmwareList, firmwareVersion):
        returnList={}
        if self.debug >= 2:
            LOG(self.silent).writeEvent(msg='Starting Firmware Version Comparison', msgType='INFO')
        if self.debug >= 3:
            LOG(self.silent).writeEvent(msg=f'JSON we have to work with at this point:\n{aciFirmwareList}', msgType='INFO')
            LOG(self.silent).writeEvent(msg=f'Firmware we are looking for: {firmwareVersion}', msgType='INFO')
        for firmware in aciFirmwareList:
            firmwareName = firmware['firmwareFirmware']['attributes']['fullVersion']
            if self.debug >= 1:
                LOG(self.silent).writeEvent(msg=f'Assessing Firmware: {firmwareName}',msgType='INFO')
            if self.debug >= 3:
                LOG(self.silent).writeEvent(msg=f'Firmware Attribute Information:\n{firmware}',msgType='INFO')
            if firmwareName == firmwareVersion:
                LOG(self.silent).writeEvent(msg=f'Firmware version {firmwareVersion} found',msgType='INFO')
                return firmware['firmwareFirmware']['attributes']['fullVersion']    
        LOG(self.silent).writeEvent(f'We did not find the firmware you would like to deploy', msgType='FAIL')
        return

    def bailOutOnNoFirmware(self, aciFirmwareList):
        LOG(self.silent).writeEvent(msg='To use this script you must specify a firmware version uploaded to the APIC to upgrade to',msgType='WARN')
        LOG(self.silent).writeEvent(msg='The following are potential options',msgType='WARN')
        for firmware in aciFirmwareList:
            if self.debug >= 3:
                LOG(self.silent).writeEvent(msg=f'Firmware Attribute Information:\n{firmware}',msgType='INFO')
            for key, value in firmware['firmwareFirmware']['attributes'].items():
                if key == 'fullVersion':
                    LOG(self.silent).writeEvent(msg=f'\t{value}', msgType='WARN')
        LOG(self.silent).writeEvent(msg="Thats all folks!!!", msgType='FAIL')
        exit()

class phase3:
    def __init__(self, silent=False):
        self.silent = silent
        return

    def confirmTimeToStart(self, minutesUntilStart):
        # Silent does not ask for input. We just skip this step if it is true
        if self.silent == True:
            return
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
                print(f"Count Down Timer: {TIMEDELTA(seconds=int(timeDifference))}",end='..\r',flush=True)
        else:
            LOG(self.silent).writeEvent(msg="Exiting without upgrading", msgType='FAIL')
            exit()
        return

# Phase 4 and phase 1 are the same. If you are looking for phase 4, go there. 

class phase5:
    # Write to the APIC to trigger the upgrade. We use the token obtained in phase 4 (repeat of phase 1) to trigger this upgrade
    def __init__(self, groups, args, cookie, firmwareVersion):
        self.debug = args.debug
        self.cookie = cookie
        self.groups = groups
        self.args = args
        self.firmwareVersion = firmwareVersion
        if self.debug >= 4:
            self.silent = False
        else:
            self.silent = args.silent
        return
    
    def upgradeSwitches(self):
        for group in self.groups:
            self.upgradeSwitch(group)
        return

    def upgradeSwitch(self, group):
        LOG(self.silent).writeEvent(msg=f"Starting switch Upgrade for the group '{group}' to firmware version {self.firmwareVersion}", msgType='INFO')
        dn = f"uni/fabric/maintpol-{group}"
        if self.debug >=2:
            LOG(self.silent).writeEvent(msg=f'DN to be modified: {dn}', msgType='INFO')
        deploymentJSON = json.dumps({
            "maintMaintP": { 
                "attributes":{
                    "dn": f"{dn}",
                    "version": f"{self.firmwareVersion}",
                    "adminSt": "triggered"
                }
            }
        })
        if self.debug >= 3:
            LOG(self.silent).writeEvent(msg=f'JSON to deploy:\n{deploymentJSON}\n')
        requestPath=f'https://{self.args.apicName}/api/mo/uni/fabric/maintpol-{group}.json'
        #Call getData to get list of firmware. 
        if self.args.failsafe == True:
            jsonResponseRAW = urlFunctions(self.args).getData(url=f'{requestPath}',requestType='post',cookie=self.cookie, data=deploymentJSON)
            if int(json.loads(jsonResponseRAW)['totalCount']) == 0:
                LOG(self.silent).writeEvent(msg='Firmware Upgrade has been triggered',msgType='INFO')
                LOG(self.silent).writeEvent(msg='Check ACI GUI for firmware upgrade status',msgType='INFO')
                if self.debug >= 2:
                    LOG(self.silent).writeEvent(msg=f'Results from change request to upgrade firmware:\n{jsonResponseRAW}',msgType='INFO')
        else:
            LOG(self.silent).writeEvent(msg='No actions was taken because failsafe was not specified. If you really want to do this specify --failsafe to execute this again.',msgType='INFO')
        return
