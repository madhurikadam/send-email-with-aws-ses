import json
import time
import calendar
import boto3
import os
import re
from botocore.exceptions import ClientError
dynamodb = boto3.resource('dynamodb')

def email_info(event,context):
    print(json.dumps(event))
    if event['httpMethod'] == 'POST':
        response = create_landing_page_customer(event)
        return response
    else:
        response = {
            "headers": set_cross_origin_headers(),
            "statusCode": 405,
            "body": "Method not supported"
        }
        #response = get_all_landing_page_users()
        return response

def get_all_landing_page_users():
    body = get_data()
    status_code = body['ResponseMetadata']['HTTPStatusCode']
    response = {
        "headers": set_cross_origin_headers(),
        "statusCode": status_code
    }
    if status_code == 200:
        response["body"] = json.dumps(body['Items'])
        print(response)
    else:
        errorMsg = {"error": "Failed to load data"}
        response["body"] = json.dumps(errorMsg)
        print(response)

    return response


def create_landing_page_customer(event):
    requestBody = json.loads(event['body'])
    response = None
    match = re.search(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', requestBody['email'], re.I)
    if None != match:
        date = str(calendar.timegm(time.gmtime()))
        body = {
            "sourceIp": event['requestContext']['identity']['sourceIp'],
            "requestDate": date,
            "userAgent": event['requestContext']['identity']['userAgent'],
            "email": requestBody['email']
        }
        resp = insert_data(body)
        print(resp)
        status_code = resp['ResponseMetadata']['HTTPStatusCode']
        response = {
                "headers": set_cross_origin_headers(),
                "statusCode": 200
                }
        if status_code == 200:
            response["body"]= None
            print(response)
        else:
            errorMsg = {"error": "Failed to add email address"}
            response["body"] = json.dumps(errorMsg)
            print(response)
    else:
        errorMsg = {"error": "Invalid email Id. Please enter correct email id"}
        response = {
            "headers": set_cross_origin_headers(),
            "statusCode": 400,
            "body": json.dumps(errorMsg)
        }
        print(response)
    return response


def insert_data(record):
    table = dynamodb.Table(os.environ.get('EMAIL_INFO_TABLE'))
    resp = table.put_item(
            Item={
                'email': record['email'],
                'requestDate': record['requestDate'],
                'userAgent': record['userAgent'],
                'sourceIp':record['sourceIp']
            }
        )
    send_email(emailTemplate(),record['email'])
    return resp
def set_cross_origin_headers():
    cross_headers =  {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": True
        }
    return  cross_headers

def get_data():
    table = dynamodb.Table(os.environ.get('EMAIL_INFO_TABLE'))
    resp = table.scan()
    return resp


def get_email_sender():
    sender = os.environ['SES_EMAIL_SENDER']
    return sender

def send_email(data, recipient):
    SENDER = get_email_sender()
    SENDER = "Prashant < {} >".format(SENDER)
    RECIPIENT = recipient
    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-west-2"
    SUBJECT = "Thanks for your interest in Unyx"
    # The HTML body of the email.
    BODY_HTML = data
    # The character encoding for the email.
    CHARSET = "UTF-8"
    # Create a new SES resource and specify a region.
    session = boto3.Session()
    client = session.client('ses', region_name=AWS_REGION)
    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    }
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER
        )
        print(response)
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

def emailTemplate():
    with open('./emailInfo/EmailTemplate.html', 'r') as f:
        html_string = f.read()
    return  html_string

