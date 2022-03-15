#!/usr/bin/python3.9
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

#Modules
#from cmath import phase
import sys, os, argparse

#Add custom modules bin directory to path
sys.path.append(os.getcwd()+'/bin')

from common import timeFunctions
from common import loggingFunctions as LOG
from aciFirmwareActions import phase1
from aciFirmwareActions import phase2a
from aciFirmwareActions import phase2b
from aciFirmwareActions import phase3
from aciFirmwareActions import phase5 # This is no phase 4, this isn't a mistake


#Clear the screen
os.system('clear')

#Default Values
defaultUser=''
defaultServer=''

#Argument Help
helpmsg = '''
This tool is intended to be run in a screen session, and will trigger an upgrade
of Cisco ACI for the designated upgrade group. 
'''

argsParse = argparse.ArgumentParser(description=helpmsg)
argsParse.add_argument('--minutes', '-m', action='store',         dest='minutesUntilStart', default=30,            help="Minutes to wait until script should start the firmware update"        )
argsParse.add_argument('--groups',    '-g', action='append',      dest='firmwareGroups',    default=[],            help='Firmware Groups you would like to upgrade with this script')
argsParse.add_argument('--aci-user',  '-u', action='store',       dest='apicUser',          default=defaultUser,   help='Provide the user name for ACI access. Default is admin')
argsParse.add_argument('--apic',      '-a', action='store',       dest='apicName',          default=defaultServer, help='Provide APIC DNS name or IP address')
argsParse.add_argument('--aci-pass',  '-p', action='store',       dest='password',          default='',            help='Enter Password for APIC access. If none provided, you will be prompted')
argsParse.add_argument('-v',	            action='count',       dest='debug',	            default=0,  	       help='Advanced Output')
argsParse.add_argument('-f',                action='store',       dest='firmwareVersion',   default='',            help='Firmware version to deploy. We give you a list of possible firmware if you enter nothing')
argsParse.add_argument('--failsafe',        action='store_true',  dest='failsafe',          default=False,         help='Firmware version to deploy. We give you a list of possible firmware if you enter nothing')
argsParse.add_argument('--silent',    '-s', action='store_true',  dest='silent',            default=False,         help='This switch allows the script to run with no output and will not request confirmation')
argsParse.add_argument('--domain',    '-d', action='store',  dest='domain',            default='',            help='Used only when a domain must be selected for authentication')
args = argsParse.parse_args()

if (args.silent == True) and (int(args.debug) < 4) and (int(args.debug != 0)):
    LOG().writeEvent(msg=f'This script cannot be run with both verbose output and silent at the same time. You have to choose.',msgType='FAIL')
    exit()

# Phase 1 (Test to be sure we can authenticate)
LOG(args.silent).writeEvent(msg=f'########## Starting Phase 1 - Testing Authentication to {args.apicName} ##########',msgType='INFO')
cookie = phase1(args).getCookie()

# Phase 2 (Test that the firmware group and firmware version we are looking for exists)
LOG(args.silent).writeEvent(msg=f'########## Starting Phase 2 - Checking Groups to see what should be updated ##########')
verifiedGroups=phase2a(cookie=cookie,args=args).verifyGroups()
verifiedFirmware=phase2b(cookie=cookie,args=args).verifyFirmware()
# We invalidate the existing cookie, because we are going to get another one when it is time to complete the firmware update.
del cookie

# Phase 3 (Confirm that the right time has been selected and then wait)
LOG(args.silent).writeEvent(msg=f'########## Starting Phase 3 - Waiting to start firmware update ##########')
phase3(silent = args.silent).confirmTimeToStart(int(args.minutesUntilStart))

# Phase 4 (Obtain Token to trigger update)
LOG(args.silent).writeEvent(msg=f'########## Starting Phase 4 - Getting a new token ##########')
#There is no difference between phase 1 and phase 4, so we just do it again
cookie = phase1(args).getCookie()

# Phase 5 (Trigger firmware update)
phase5(cookie=cookie, args=args, groups=verifiedGroups, firmwareVersion=verifiedFirmware).upgradeSwitches()
# Phase 6 (Validate that firmware update has started)
