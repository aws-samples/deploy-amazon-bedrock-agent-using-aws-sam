# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0


import os

import boto3
from aws_lambda_powertools import Metrics, Logger, Tracer
from datetime import datetime, timedelta

from model import get_park_reservations, write_park_reservation


logger = Logger()
tracer = Tracer()
metrics = Metrics()

table_name = os.environ['DDB_TABLE']
table = boto3.resource('dynamodb').Table(table_name)


@tracer.capture_method
def get_available_park_days(park_id, start_date, end_date):
    """
        This queries the datastore to find available park days within a date range.

        Parameters:
        park_id (str): The id of the park you want to check for availability
        start_date (str): The start date for the date range to query
        start_date (str): The end date of the range to query

        Returns:
        [str]: List of dates that the park is available
        """

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        response = get_park_reservations(park_id, start_date, end_date, table)
        reservations = [reservation['sk'].replace('R', '').replace('#', '') for reservation in response]
        logger.info(reservations)

        all_days = set((start_date + timedelta(days=x)).strftime("%Y-%m-%d") for x in range((end_date - start_date).days + 1))

        for reservation in reservations:
            logger.info(reservation)
            res_date = datetime.strptime(reservation, '%Y-%m-%d').strftime("%Y-%m-%d")
            if len(all_days) > 0 and str(res_date) in all_days:
                all_days.remove(str(res_date))

        available_days = sorted(list(all_days))

        return available_days
    except Exception as e:
        raise Exception(f"Error occurred: {e}")


@metrics.log_metrics(capture_cold_start_metric=True)
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    """
    This function handles requests for the park reservation tool.

    Parameters:
    event (dict): The details and metadata for the request
    context (dict): additional context for the request

    Returns:
    response (dict): The response for the tool
    """
    logger.info(event)

    # agent = event['agent']
    actionGroup = event['actionGroup']
    function = event['function']
    parameters = event.get('parameters', [])
    responseBody = {
        "TEXT": {
            "body": "Error, no function was called"
        }
    }

    if function == 'get_available_park_days':
        park_id = None
        start_date = None
        end_date = None
        for param in parameters:
            if param["name"] == "park_id":
                park_id = param["value"]
            if param["name"] == "start_date":
                start_date = param["value"]
            if param["name"] == "end_date":
                end_date = param["value"]

        if not all([park_id, start_date, end_date]):
            raise Exception("Missing mandatory parameters: park_id, start_date, end_date")

        available_days = get_available_park_days(park_id, start_date, end_date)
        responseBody = {
            'TEXT': {
                "body": f"Available days for park ID {park_id} between {start_date} and {end_date}: {available_days}"
            }
        }
    elif function == 'book_park':
        citizen_id = None
        park_id = None
        reservation_date = None
        for param in parameters:
            if param["name"] == "citizen_id":
                citizen_id = param["value"]
            if param["name"] == "park_id":
                park_id = param["value"]
            if param["name"] == "reservation_date":
                reservation_date = param["value"]

        session_citizen_id = session_attributes.get('citizenID', '')
        if not session_citizen_id == '':
            citizen_id = session_citizen_id # override with the session attributes if available

        if not all([citizen_id, park_id, reservation_date]):
            raise Exception("Missing mandatory parameters: citizen_id, park_id, reservation_date")

        response = write_park_reservation(
            park_id=park_id,
            reservation_date=reservation_date,
            citizen_id=citizen_id,
            table=table
        )

        logger.info(response)

        responseBody = {
            'TEXT': {
                "body": f"Created reservation for customer_id: {citizen_id} at park_id: {park_id} on {reservation_date}"
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