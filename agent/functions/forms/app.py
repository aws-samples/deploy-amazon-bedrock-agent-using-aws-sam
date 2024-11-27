# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from tarfile import version

import boto3
from aws_lambda_powertools import Metrics, Logger, Tracer

from model import start_form_version, submit_form_version, write_form_field, get_form_fields


logger = Logger()
tracer = Tracer()
metrics = Metrics()

table_name = os.environ['DDB_TABLE']
table = boto3.resource('dynamodb').Table(table_name)

forms_bucket = os.environ['FORMS_INGEST_BUCKET']

@metrics.log_metrics(capture_cold_start_metric=True)
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    """
    This function handles requests for the forms processing tool.

    Parameters:
    event (dict): The details and metadata for the request
    context (dict): additional context for the request

    Returns:
    response (dict): The response for the tool
    """
    logger.info(event)

    agent = event['agent']
    actionGroup = event['actionGroup']
    function = event['function']

    parameters = event.get('parameters', [])
    citizen_id = None
    form_template_id = None
    version_id = None
    form_field_id = None
    form_field_value = None

    for param in parameters:
        if param["name"] == "citizen_id":
            citizen_id = param["value"]
        elif param["name"] == "form_template_id":
            form_template_id = param["value"]
        elif param["name"] == "version_id":
            version_id = param["value"]
        elif param["name"] == "form_field_id":
            form_field_id = param["value"]
        elif param["name"] == "form_field_value":
            form_field_value = param["value"]

    if function == 'start_new_form':
        if not (form_template_id and citizen_id):
            raise Exception("Missing required citizen_id or form_template_id")
        version_id = start_form_version(
            form_template_id=form_template_id,
            citizen_id=citizen_id,
            table=table
        )
        logger.info(f"Created  version {version_id} of form {form_template_id} for {citizen_id} on table {table}")

        response_body = {
            'TEXT': {
                "body": f"Created  version {version_id} of form {form_template_id} for {citizen_id}"
            }
        }
    elif function == 'get_form_fields':
        if not (form_template_id):
            raise Exception("Missing required form_template_id")
        fields = get_form_fields(
            form_template_id=form_template_id,
            table=table
        )
        logger.info(fields)

        response_body = {
            'TEXT': {
                "body": str(fields)
            }
        }
    elif function == 'submit_form':
        if not (form_template_id and citizen_id and version_id):
            raise Exception("Missing required citizen_id or form_template_id or version_id")
        version_id = submit_form_version(
            form_template_id=form_template_id,
            citizen_id=citizen_id,
            version_id=version_id,
            table=table
        )
        logger.info(f"Submitted  version {version_id} of form {form_template_id} for {citizen_id} on table {table}")

        response_body = {
            'TEXT': {
                "body": f"Submitted  version {version_id} of form {form_template_id} for {citizen_id}"
            }
        }
    elif function == 'update_form_field':
        if not (form_template_id and citizen_id and version_id and form_field_id and form_field_value):
            raise Exception("Missing required citizen_id or form_template_id or version_id or field_id or field_value")
        write_form_field(
            form_template_id=form_template_id,
            citizen_id=citizen_id,
            version_id=version_id,
            field_id=form_field_id,
            data=form_field_value,
            table=table
        )




    action_response = {
        'actionGroup': actionGroup,
        'function': function,
        'functionResponse': {
            'responseBody': response_body
        }
    }

    function_response = {'response': action_response, 'messageVersion': event['messageVersion']}
    logger.info("Response: {}".format(function_response))

    return function_response

