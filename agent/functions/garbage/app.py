# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import boto3
from aws_lambda_powertools import Metrics, Logger, Tracer

from model import get_garbage_route_by_district_id, write_bulk_waste_request


logger = Logger()
tracer = Tracer()
metrics = Metrics()

table_name = os.environ['DDB_TABLE']
table = boto3.resource('dynamodb').Table(table_name)


@metrics.log_metrics(capture_cold_start_metric=True)
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    """
    This function handles requests for the garbage management tool.

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
    session_attributes = event.get('sessionAttributes', {})
    responseBody = {
        "TEXT": {
            "body": "Error, no function was called"
        }
    }

    if function == 'get_garbage_pickup_day':
        district_id = None
        for param in parameters:
            if param["name"] == "district_id":
                district_id = param["value"]

        if 'districtID' in session_attributes.keys():
            session_district_id = session_attributes.get('districtID', '')
            if not session_district_id == '':
                district_id = session_district_id  # override with the session attributes if available

        if not district_id:
            raise Exception("Missing mandatory parameter: district_id")

        route = get_garbage_route_by_district_id(district_id, table)
        responseBody = {
            'TEXT': {
                "body": f"Garbage pickup route for district ID {district_id}: {route}"
            }
        }
    elif function == 'schedule_bulk_pickup':
        citizen_id = None
        pickup_date = None
        garbage_route = None

        for param in parameters:
            if param["name"] == "citizen_id":
                citizen_id = param["value"]
            elif param["name"] == "pickup_date":
                pickup_date = param["value"]
            elif param["name"] == "garbage_route":
                garbage_route = param["value"]

        session_citizen_id = session_attributes.get('citizenID', '')
        if not session_citizen_id == '':
            citizen_id = session_citizen_id  # override with the session attributes if available

        response = write_bulk_waste_request(
            citizen_id=citizen_id,
            pickup_date=pickup_date,
            garbage_route=garbage_route,
            table=table
        )
        logger.info(response)

        responseBody = {
            'TEXT': {
                "body": f"Bulk waste pickup requested for {citizen_id} {pickup_date} {garbage_route}"
            }
        }

    action_response = {
        'actionGroup': actionGroup,
        'function': function,
        'functionResponse': {
            'responseBody': responseBody
        }
    }

    function_response = {'response': action_response, 'messageVersion': event['messageVersion']}
    logger.info("Response: {}".format(function_response))

    return function_response