import eesdk
from datetime import date
import boto3
import os

# Function to get required EE API Information from the central (this) account
def getEEAPIInfo(value):
    cfn_client = boto3.client('cloudformation')
    response = cfn_client.describe_stacks()
    response = response['Stacks'][0]['Parameters']
    i=0
    for items in response:
        if response[i]['ParameterKey'] == value:
            return response[i]['ParameterValue']
        i=i+1

# Retrieve event specific API information
api_token=getEEAPIInfo('EEAPIToken')
event_id=getEEAPIInfo('EEEventId')
module_id=getEEAPIInfo('EEModuleId')

def getOutputs(reg,api_token,event_id,module_id):
    sdk = eesdk.EESDK("https://api.eventengine.run", api_token, event_id, module_id)
    teams = sdk.get_all_teams()
    dt = str(date.today())
    f=open("Outputs "+reg+" "+dt+".txt", "a")
    object_name = os.path.basename(fname)
    for team in teams:
        team_id = team['team-id']
        xa_sess = sdk.assume_team_ops_role(team_id)
        team_cfn_client = xa_sess.client('cloudformation',region_name=reg)
        response = team_cfn_client.describe_stacks()
        if response['Stacks'][0]['StackStatus'] != 'CREATE_COMPLETE':
            f.write(str("Stack error "+response['Stacks'][0]['StackStatus']+" for account "+team_id))
        if response['Stacks'][0]['StackStatus'] == 'CREATE_IN_PROGRESS':
            print(response['Stacks'][0]['StackStatus']+" for account "+team_id)
            #f.write(str(response['Stacks'][0]['StackStatus']+" for account "+team_id))
        else:
            outputs = response['Stacks'][0]['Outputs']
            f.write(str(outputs))
    return object_name

# Create a bucket for the Outputs
bucket_name = ('aviatrix-immersion-day-outputs-'+str(date.today()))
s3_client = boto3.client('s3')
response = s3_client.create_bucket(
    ACL='private',
    Bucket=bucket_name,
    CreateBucketConfiguration={
        'LocationConstraint': 'us-west-2'
    }
)
def putOutputs(bucket_name,fname):
    s3_resource = boto3.resource('s3')
    s3_resource.Bucket(bucket_name).upload_file(
        Filename=fname,
        Key=fname
    )

# Get outputs for the control stack in us-west-2 and put them in an S3 bucket
fname = getOutputs("us-west-2",api_token,event_id,module_id)
# Put outputs in local S3
putOutputs(bucket_name,fname)
# Repeat for us-east-1
fname = getOutputs("us-east-1",api_token,event_id,module_id)
putOutputs(bucket_name,fname)
