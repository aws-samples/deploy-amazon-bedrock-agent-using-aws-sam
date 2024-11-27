# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import boto3
import json
import shortuuid
import datetime
import time
from collections import defaultdict

from aws_lambda_powertools import Metrics, Logger, Tracer

# from model import get_garbage_route_by_district_id, write_bulk_waste_request
from model import start_form_version, write_form_template_field, write_form_template, get_form_fields


logger = Logger()
tracer = Tracer()
metrics = Metrics()

table_name = os.environ['DDB_TABLE']
table = boto3.resource('dynamodb').Table(table_name)

textract = boto3.client('textract')

forms_bucket = os.environ['FORMS_INGEST_BUCKET']

def create_new_form_template():
    """
    This function initializes a new form template in the application datastore.

    Parameters: form_template_id (str)

    Returns:
    fields [str]: The fields in the form
    """
    form_template_id = shortuuid.uuid()
    timestamp = str(datetime.datetime.now())
    data = f"Created {timestamp}"
    logger.info(f"Creating new Form Template assigning id {form_template_id} at {timestamp}")
    write_form_template(form_template_id, data, table)
    return form_template_id

def start_textract_analysis_job(s3_bucket, s3_key):
    """
    This function starts the Amazon Textract job

    Parameters:
    form_location_s3_bucket (str): The S3 bucket storing the form template
    form_location_s3_key (str): The S3 key for the template

    Returns:
    jobId str: The job id for the Amazon Textract job
    """
    response = textract.start_document_analysis(
        DocumentLocation={"S3Object": {
            "Bucket": s3_bucket,
            "Name": s3_key
        }},
        FeatureTypes=["FORMS"]
    )
    return response['JobId']

def get_textract_result_or_status(job_id):
    """
    This function starts the Amazon Textract job

    Parameters:
    job_id (str): The JobId for the Amazon Textract job

    Returns:
    response dict: The job response
    """
    response = textract.get_document_analysis(
        JobId=job_id,
    )
    return response


def wait_for_textract_result(job_id):
    """
    This function loops until the job with id job_id is complete

    Parameters:
    job_id (str): The JobId for the Amazon Textract job

    Returns:
    response dict: The job response
    """
    response = get_textract_result_or_status(job_id)
    status = response['JobStatus']
    if status == "IN_PROGRESS":
        logger.info(f"Waiting for textract job_id: {job_id}")
        time.sleep(2)
        return (wait_for_textract_result(job_id))
    return response

def find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
    return value_block

def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X '

    return text

def get_form_fields_from_doc(form_location_s3_bucket, form_location_s3_key):
    """
    This function extracts fields from forms that are stored in Amazon S3 using Amazon Transcribe.

    Parameters:
    form_location_s3_bucket (str): The S3 bucket storing the form template
    form_location_s3_key (str): The S3 key for the template

    Returns:
    fields [str]: The fields in the form
    """
    job_id = start_textract_analysis_job(
        s3_bucket=form_location_s3_bucket,
        s3_key=form_location_s3_key
    )
    textract_response = wait_for_textract_result(job_id)

    blocks = textract_response['Blocks']

    key_map = {}
    value_map = {}
    block_map = {}
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    kvs = defaultdict(list)
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key].append(val)

    return list(kvs.keys())


@metrics.log_metrics(capture_cold_start_metric=True)
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    """
    This function handles forms ingestion.

    Parameters:
    event (dict): The details and metadata for the request
    context (dict): additional context for the request

    Returns:
    response (dict): The response for the tool
    """

    logger.info(event)
    logger.info(event.keys())

    form_template_id = create_new_form_template()
    logger.info(f"Populating form with id {form_template_id}")

    records = event['Records']

    for record in records:
        key = record['s3']['object']['key']
        logger.info(f"Processing file: {key}")
        form_fields = get_form_fields_from_doc(forms_bucket, key)
        logger.info("Found fields: {form_fields}")
        logger.info(form_fields)

        for i, field in enumerate(form_fields):
            logger.info(f"Adding field: {field}")
            write_form_template_field(
                form_template_id=form_template_id,
                field_id=i,
                data=json.dumps({
                    "field_name": field,
                    "is_required": False
                }),
                table=table
            )







