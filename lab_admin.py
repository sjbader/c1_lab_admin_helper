#! /usr/bin/python3

# Import our required modules
import os
import time
import json
import re
import sys
from terrasnek.api import TFC

# Get variables from the OS environment
TFC_TOKEN = os.getenv("TFC_TOKEN", None)
TFC_URL = os.getenv("TFC_URL", "https://app.terraform.io")
TFC_ORG = os.getenv("TFC_ORG", None)


# Run Payload Template
run_payload_template = {
    "data": {
        "attributes": {
            "message": "Run from Python Lab Admin Script",
            "auto-apply": True
        },
        "type": "runs",
        "relationships": {
            "workspace": {
                "data": {
                   "type": "workspaces"
                }
            }
        }
    }
}


# Function to monitor the status of a run
def run_status(api, run_id, ws_name):
    break_regex = r"planned_and_finished|applied|policy_soft_failed|discarded|canceled|errored|force_canceled|applied"
    seconds = 0
    total_time = 0
    last_status = ''
    print(f'\nRun on {ws_name} is starting!')
    url = f'https://app.terraform.io/app/{TFC_ORG}/workspaces/{ws_name}/runs/{run_id}'
    print(f'You can monitor this run at: {url}')
    while 1:
        time.sleep(1)
        seconds += 1
        total_time += 1
        run_status = api.runs.show(run_id)
        # dump = json.dumps(run_status, indent =4)
        # print(dump)
        if last_status != run_status["data"]["attributes"]["status"]:
            last_status = run_status["data"]["attributes"]["status"]
            seconds = 0
            print(f'\n\t{last_status} - {seconds} seconds elapsed', end='\r')
        else:
            print(f'\t{last_status} - {seconds} seconds elapsed', end='\r')
        if re.match(break_regex, last_status):
            print(f'\n\nFinished - Status: {last_status} - Approximate total time elapsed: {total_time} seconds\n')
            break


# Function to apply a run
def apply_run(api, ws_id, payload, workspaces):
    run = api.runs.create(payload)
    run_id = run["data"]["id"]
    ws_name = workspaces[ws_id]
    run_status(api, run_id, ws_name)


# Function to print help
def print_help():
    string = f'''
    You can run this program without any arguments to enter interactive mode.

    The environment variables TFC_ORG and TFC_TOKEN must be set properly, or this program will not work.

    If you want to call this program from another script, use the -a argument with the
    following parameters:
        action_type         = Either 'apply' or 'destroy'
        workspace_id        = The workspace ID to run the action against (can be obtained via Terraform Web UI or interactive mode of this program)

    For example:
        python3 lab_admin.py -a apply ws-iWrmrc5TZkTCBLhP

    You can also pass just a -l argument to list all workspaces

    For example:
        python3 lab_admin.py -l
    '''
    print(string)

    
# Main function
def main():
    # Get command line arguments and determine next steps
    # This got pretty ugly, but it works!
    automation = False
    only_list = False
    if len(sys.argv) > 1:
        if len(sys.argv) == 4 and sys.argv[1] == '-a':
            automation = True
            # Use regex to validate we received sane input
            if re.match(r"apply|destroy", sys.argv[2], flags=re.IGNORECASE) and re.match(r"^ws-.*", sys.argv[3], flags=re.IGNORECASE):
                # This means our input was valid so we assign our variables
                action_type = sys.argv[2]
                if action_type == "apply":
                    run_type = 'a'
                elif action_type == "destroy":
                    run_type = 'd'
                else:
                    # We should never get here, but if we do, quit
                    print("Action type mismatch!")
                    print_help()
                    quit()

                ws_id = sys.argv[3]
            else:
                print("Invalid input!")
                print_help()
                quit()
        elif sys.argv[1] == '-l':
            # We are doing a list-only run
            only_list = True
        elif len(sys.argv) != 4:
            print_help()
            quit()
        else:
            print("Invalid arguments sent!")
            print_help()
            quit()
    
    # Connect to the API and set our organization
    api = TFC(TFC_TOKEN, url=TFC_URL)
    api.set_org(TFC_ORG)


    # Get a list of all the workspaces
    workspace_json = api.workspaces.list_all(search=None, include=None, filters=None)
    data = json.dumps(workspace_json, indent=4)

    # print(data) # Use this to debug the json response
    # Loop throught the list of workspaces and print the name and ID
    # We skip outputting data if we're using automation
    workspaces = {}
    for i in workspace_json["data"]:
        workspaces[i["id"]] = i["attributes"]["name"]
        if not automation:
            print(f'Workspace ID: {i["id"]}   Name: {i["attributes"]["name"]}')
    # Exit if we're just listing
    if only_list:
        quit()


    # Get the ID of the workspace to work on - require user input (if we're not using automation)
    while True:
        if not automation:
            ws_id = input('\nEnter the Workspace ID of the workspace you want to control: ')
        if len(ws_id) != 0:
            break
        else:
            continue

    # Set the workspace ID in the run payload
    run_payload = run_payload_template
    run_payload["data"]["relationships"]["workspace"]["data"]["id"] = ws_id

    # IKS regex match string
    # Match something-IKS-something or something-IKS, but not something-IKSsomething
    iks_match_string = r"(.*-IKS-.*$)|(.*-IKS$)"

    # Determine the run type
    while True:
        if not automation:
            run_type = input('Enter D for a destroy run, A for an apply run, or E to exit: ')
        if run_type.casefold() == 'a':
            # Check to see if it's an IKS run
            if re.match(iks_match_string, workspaces[ws_id], flags=re.IGNORECASE):
                # Doing an IKS run - which is goofy, we have to set variables instead of a normal apply and destroy
                print("\n!!! This is an IKS run. Starting run with action_type = Unassign")
                run_variables = [{"key": "action_type", "value": "\"Unassign\""}]
                run_payload["data"]["attributes"]["variables"] = run_variables
                apply_run(api, ws_id, run_payload, workspaces)
                print("Sleeping for 10 seconds to allow Intersight to finish")
                time_seconds = 10
                for i in range(time_seconds):
                    sys.stdout.write('.')
                    sys.stdout.flush()
                    time.sleep(1)
                print("\n\n!!! Starting a new run with action_type = Deploy")
                run_variables = [{"key": "action_type", "value": "\"Deploy\""}]
                run_payload["data"]["attributes"]["variables"] = run_variables
                apply_run(api, ws_id, run_payload, workspaces)
                print("!!! Even though Terraform has completed, Intersight will need to finish deploying the IKS cluster.")
                print("!!! It typically takes Intersight IKS 20-40 minutes to deploy the cluster completely")
                print("!!! You can check the Intersight status at https://www.intersight.com\n")
                break
            else:
                # Do a normal run (non-IKS)
                apply_run(api, ws_id, run_payload, workspaces)
                break
        elif run_type.casefold() == 'd':
            if re.match(iks_match_string, workspaces[ws_id], flags=re.IGNORECASE):
                # Doing an IKS run, which is not a normal destroy, instead we set action_type = Delete
                print("\n!!! This is an IKS run. Starting run with action_type = Delete")
                run_payload["data"]["attributes"]["message"] = "Destroy run from Python Lab Admin Script"
                run_variables = [{"key": "action_type", "value": "\"Delete\""}]
                run_payload["data"]["attributes"]["variables"] = run_variables
                apply_run(api, ws_id, run_payload, workspaces)
                print("!!! Even though Terraform has completed, Intersight will need to finish destroying the IKS cluster.")
                print("!!! It typically takes Intersight IKS 10-20 minutes to destroy the cluster completely.")
                print("!!! You can check the Intersight status at https://www.intersight.com\n")
                break
            else:
                # Do a destroy run
                run_payload["data"]["attributes"]["is-destroy"] = True
                run_payload["data"]["attributes"]["message"] = "Destroy run from Python Lab Admin Script"
                apply_run(api, ws_id, run_payload, workspaces)
                break
        elif run_type.casefold() == 'e':
            quit()
        else:
            continue


# Run our main function
if __name__ == '__main__':
    main()
