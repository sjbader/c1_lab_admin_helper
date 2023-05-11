# C1 Lab Admin Script

This script can be used to stop and start EKS and IKS labs that are hosted on Terraform Cloud.

## Requirements

Install Terrasnek:

```
pip install terrasnek
```

Set environment variables:
```
export TFC_TOKEN="Token from TFC"
export TFC_ORG="Organization from TFC"
```

Then you can simply run the script manually:
```
python3 lab_admin.py
```

You can also give all arguments on the command line
```
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
```
