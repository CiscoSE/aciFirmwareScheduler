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
import sys, os, argparse

#Add custom modules bin directory to path
sys.path.append(os.getcwd()+'/bin')

from common import timeFunctions
from common import loggingFunctions as LOG
from common import urlFunctions

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
argsParse.add_argument('--starttime', '-t', action='store',      dest='firmwareStartTime',                    help="Start time for firmware update"        )
argsParse.add_argument('--groups',    '-g', action='append',     dest='firmwareGroup', default=[],            help='Provide a list of IPv4 addresses to search for (one or many)')
argsParse.add_argument('--aci-user',  '-u', action='store',      dest='apicUser',     default=defaultUser,   help='Provide the user name for ACI access. Default is admin')
argsParse.add_argument('--apic',      '-a', action='store',      dest='apicName',    default=defaultServer, help='Provide APIC DNS name or IP address')
argsParse.add_argument('--aci-pass',  '-p', action='store',      dest='password',      default='',            help='Enter Password for APIC access. If none provided, you will be prompted')
argsParse.add_argument('-debug',	        action='store_true', dest='debug',	       default=False, 	      help='Advanced Output')
#argsParse.add_argument('-d',         action='store',      dest='directory',  default='./',               help='Directory to write csv report to')
args = argsParse.parse_args()

# Phase 1 (Test to be sure we can authenticate)
LOG().writeEvent(msg=f'########## Starting Phase 1 - Testing Authentication to {args.apicName} ##########')
URL = urlFunctions(args=args)
cookie = URL.getCookie()
if cookie:
    if args.debug:
        # We only print the cookie if we are in debug mode
        print(f"Cookie:\n{cookie}")
    # We print status either way.    
    LOG().writeEvent(msg='Cookie Obtained', msgType="INFO")
else:
    LOG().writeEvent(msg='Cookie was not obtained', msgType='FAIL')
    exit()
# Phase 2 (Test that the firmware group we are looking for exists)


# Phase 3 (Confirm that the right time has been selected)

# Phase 4 (Provide a count down timer)

# Phase 5 (Obtain Token to trigger update)

# Phase 6 (Trigger firmware update)

# Phase 7 (Validate that firmware update has started)
