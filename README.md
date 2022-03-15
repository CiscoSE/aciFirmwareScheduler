# aciFirmwareScheduler
Used to schedule ACI firmware updates after 5.x release

## Concept of Operation
This script is meant to be run in one of two ways:

1.  Run this script in a screen session. This allows the script to continue to run after the user is disconnected. The script will run until the intended start time once approved by the admin running script.
2.  Run this script as a cron job using the silent mode. You get no verification using this method, and the admin must be sure all entries are correct before running.

We recommend you run this job in a screen session because the you can validate that the group exists and the right firmware has been selected. 

In all instances, the groups needed to be created in ACI prior to running this script. The script takes the group(s) given and the firmware version given, and validates they exist. When both exist you are asked to confirm that you want to proceed. By default the script waits 30 minutes, though you can run immediately, or specify the number of minutes to wait before the script runs. 

## Prerequisites 
This has been tested with Python 3.9 and the following additional elements:
1. Screen (Available on Ubuntu and CentOS)
2. Python Requests module (Install with PIP3 module if not installed by default)

## Examples
<h2 align="center">Example 1</h2>
To see which groups are available, you can run the script with minimal switches. This example makes no changes and will just output a list of known Firmware groups created in ACI.

```
python3 ./aciUpgradeScheduler.py -a SomeApicIP -u SomeAPICUser -p 'SomeAPICPassword'
```
<h2 align="center">Example 2</h2>
To see which firmware is available, provide the minimum switches noted in example one, plus at least one group created in ACI. Note that the group is case sensitive. Again, this command will make no changes because no firmware is selected:

```
python3 ./aciUpgradeScheduler.py -a SomeApicIP -u SomeAPICUser -p 'SomeAPICPassword' -g 'SomeGroup'
```
<h2 align="center">Example 3</h2>
To trigger a firmware upgrade to version 5.2(3e), use the command below. In this case we are waiting 4 hours to start the upgrade and must approve the script to continue once the firmware and group has been verified. The script will not make changes without the failsafe switch, We run this script in screen so that we are not dependent on the ssh session remaining open for 4 hours. A count down timer tells you time to execution, and you must confirm the actions before the timer starts:

```
screen
python3 ./aciUpgradeScheduler.py -a SomeApicIP -u SomeAPICUser -p 'SomeAPICPassword' -g 'SomeGroup' -m 240 -f 'n9000-15.2(3e)' --failsafe
```
<h2 align="center">Example 4</h2>
To deploy firmware as a cron job, you need to run the script in silent mode in order to ensure you are not prompted to continue and to suppress all screen output. Since the job is being scheduled externally, we set the time to zero so it runs immediately. The script still checks for groups and firmware versions, but provides no output in the event of failure. 

```
python3 ./aciUpgradeScheduler.py -a SomeApicIP -u SomeAPICUser -p 'SomeAPICPassword' -g 'SomeGroup' -m 0 -f 'n9000-15.2(3e)' --failsafe --silent
```


