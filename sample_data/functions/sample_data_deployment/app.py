# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os

import cfnresponse
import boto3


from model import get_park_reservations, write_park_reservation, write_to_ddb

def upload_to_knowledgebase(s3_bucket):
    print(f"Uploading data to knowledgebase bucket: {s3_bucket}")

    files_to_upload = [f for f in os.listdir('assets') if f.endswith('.pdf')]
    print(f"Files to upload: {files_to_upload}")

    s3_client = boto3.client('s3')
    for f in files_to_upload:
        print(f"Uploading file: {f}")
        response = s3_client.upload_file(os.path.join('assets', f), s3_bucket, f)
        print(response)
        print(f"Uploaded file: {f}")

    print(f"Uploads complete")

def delete_samples_from_knowledgebase(s3_bucket):
    print(f"Deleting data from knowledgebase bucket: {s3_bucket}")

    files_to_upload = [f for f in os.listdir('assets') if f.endswith('.pdf')]
    print(f"Files to delete: {files_to_upload}")

    s3_client = boto3.client('s3')
    for f in files_to_upload:
        try:
            print(f"Deleting file: {f}")
            response = s3_client.delete_object(
                Bucket=s3_bucket,
                Key=f
            )
            print(response)
            print(f"Deleted file: {f}")
        except:
            print(f"Error deleting {f} - continuing")

    print(f"Uploads complete")

def create_trash_routes(table_name):
    print(f"Populating records into table: {table_name}")
    table = boto3.resource('dynamodb').Table(table_name)

    yellow_route = [ {"pk": f"T{district_id}#", "sk": f"T{district_id}#", "data": "Yellow"} for district_id in [
        'A1', 'A2', 'A3', 'A4']
    ]

    blue_route = [ {"pk": f"T{district_id}#", "sk": f"T{district_id}#", "data": "Blue"} for district_id in [
        'A5', 'A6', 'B3', 'B4']
    ]

    orange_route = [ {"pk": f"T{district_id}#", "sk": f"T{district_id}#", "data": "Orange"} for district_id in [
        'B1', 'B2', 'C1', 'C2']
    ]

    green_route = [ {"pk": f"T{district_id}#", "sk": f"T{district_id}#", "data": "Green"} for district_id in [
        'C3', 'C4', 'C5', 'C6']
    ]

    red_route = [{"pk": f"T{district_id}#", "sk": f"T{district_id}#", "data": "Red"} for district_id in [
        'D3', 'D4', 'D5', 'D6']
                   ]

    items = yellow_route + blue_route + orange_route + green_route + red_route

    for item in items:
        print(f"Writing item to ddb: {item}")
        write_to_ddb(item, table)
        print(f"Wrote item to ddb: {item}")

    write_park_reservation("P1", "2024-12-03", "C1", table)
    write_park_reservation("P1", "2024-12-04", "C2", table)
    write_park_reservation("P1", "2024-12-05", "C3", table)
    write_park_reservation("P1", "2024-12-07", "C4", table)
    write_park_reservation("P1", "2024-12-08", "C5", table)
    write_park_reservation("P1", "2024-12-09", "C1", table)
    write_park_reservation("P1", "2024-12-10", "C1", table)
    write_park_reservation("P1", "2024-12-11", "C2", table)
    write_park_reservation("P1", "2024-12-13", "C4", table)
    write_park_reservation("P1", "2024-12-14", "C1", table)
    write_park_reservation("P1", "2024-12-18", "C5", table)
    write_park_reservation("P1", "2024-12-19", "C5", table)
    write_park_reservation("P1", "2024-12-23", "C4", table)
    write_park_reservation("P1", "2024-12-24", "C11", table)
    write_park_reservation("P1", "2024-12-25", "C111", table)
    write_park_reservation("P1", "2024-12-26", "C109", table)
    write_park_reservation("P1", "2024-12-29", "C31", table)
    write_park_reservation("P2", "2024-12-13", "C201", table)
    write_park_reservation("P3", "2024-12-12", "C10", table)
    write_park_reservation("P4", "2024-12-09", "C111", table)
    write_park_reservation("P5", "2024-12-03", "C1", table)
    write_park_reservation("P6", "2024-12-04", "C2", table)
    write_park_reservation("P7", "2024-12-05", "C3", table)
    write_park_reservation("P7", "2024-12-07", "C4", table)
    write_park_reservation("P7", "2024-12-08", "C5", table)
    write_park_reservation("P7", "2024-12-09", "C1", table)
    write_park_reservation("P7", "2024-12-10", "C1", table)
    write_park_reservation("P7", "2024-12-11", "C2", table)
    write_park_reservation("P7", "2024-12-13", "C4", table)
    write_park_reservation("P7", "2024-12-14", "C1", table)
    write_park_reservation("P7", "2024-12-18", "C5", table)
    write_park_reservation("P7", "2024-12-19", "C5", table)
    write_park_reservation("P7", "2024-12-23", "C4", table)
    write_park_reservation("P7", "2024-12-24", "C11", table)
    write_park_reservation("P8", "2024-12-25", "C111", table)
    write_park_reservation("P8", "2024-12-26", "C109", table)
    write_park_reservation("P8", "2024-12-29", "C31", table)
    write_park_reservation("P8", "2024-12-13", "C201", table)
    write_park_reservation("P8", "2024-12-12", "C10", table)
    write_park_reservation("P8", "2024-12-09", "C111", table)

    print("Wrote items to dynamodb")

def sync_knowledgebase(kb_id, datasource_id):
    print(f"Syncing knowledgebase: {bk_id}")
    response = client.start_ingestion_job(
        knowledgeBaseId=bk_id,
        dataSourceId=datasource_id
    )
    print(response)

def prepare_agent(agent_id):
    print(f"Preparing agent: {agent_id}")
    response = bedrock_client.prepare_agent(agentId=agent_id)
    print(response)

def lambda_handler(event, context):
    print("Loading sample data")
    print(event)
    action = event['RequestType']
    props = event['ResourceProperties']
    s3_bucket = props['s3_bucket']
    table_name = props['table_name']
    agent_id = props['agent_id']
    datasource_id = props['datasource_id']
    kb_id = props['kb_id']

    if action == "Create":
        try:
            print(f"Got DynamoDB Table Name: {table_name}")

            create_trash_routes(table_name)

            print(f"Got S3 Bucket: {s3_bucket}")

            upload_to_knowledgebase(s3_bucket)

            print("Sending success response to cloudformation")
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {"response": "OK"}, f"sample_data_{s3_bucket}_{table_name}")

            # print("Syncing knowledgebase")
            # sync_knowledgebase(kb_id, datasource_id)
            #
            # print("Preparing agent")
            # prepare_agent(agent_id)
        except:
            cfnresponse.send(event, context, cfnresponse.FAILED, {"response": "FAILED"}, f"sample_data_{s3_bucket}_{table_name}")
    elif action == "Delete":
        try:
            print(f"Got S3 Bucket: {s3_bucket}")

            delete_samples_from_knowledgebase(s3_bucket)

            print("Sending success response to cloudformation")
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {"response": "OK"},
                             f"sample_data_{s3_bucket}_{table_name}")
        except:
            print(f"Errors cleaning sample data from {s3_bucket}")
            cfnresponse.send(event, context, cfnresponse.FAILED, {"response": "FAILED"},
                             f"sample_data_{s3_bucket}_{table_name}")


