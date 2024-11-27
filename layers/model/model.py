# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import shortuuid
from boto3.dynamodb.conditions import Key


FACETS = {
    "Sales": "S",
    "Resourcing": "R",
    "Marketing": "M",
    "Product": "P",
}


def write_to_ddb(item, table):
    response = table.put_item(Item=item)
    if not response['ResponseMetadata']['HTTPStatusCode'] == 200:
        raise Exception("Error writing to DDB")
    return response

def get_item_by_key(pk, sk, table):
    return table.get_item(Key={'pk': pk, 'sk': sk})

def get_user(uid, table):
    return get_item_by_key(pk=uid, sk=uid, table=table)

def get_garbage_route_by_district_id(district_id, table):
    pk = f"T{district_id}#"
    sk = f"T{district_id}#"
    return get_item_by_key(pk, sk, table)

def get_park_reservation(park_id, start_date, end_date, table):
    return get_item_by_key(
        pk=f"P{park_id}#",
        sk=f"RS{start_date}#E{end_date}#",
        table=table
    )

def get_park_reservations(park_id, start_date, end_date, table):
    pk = f"P{park_id}#"
    # sk=R{start_date}#{end_date}#
    reservations = table.query(
        KeyConditionExpression=Key('pk').eq(pk) & Key('sk').begins_with(f"R")
    )
    return reservations['Items']

def write_park_reservation(park_id, reservation_date, citizen_id, table):
    return write_to_ddb(
            item={
                "pk": f"P{park_id}#",
                "sk": f"R{reservation_date}#",
                "data": citizen_id
            },
            table=table
        )

def write_bulk_waste_request(garbage_route, pickup_date, citizen_id, table):
    return write_to_ddb(
            item={
                "pk": f"G{garbage_route}#",
                "sk": f"R{pickup_date}#C{citizen_id}#",
                "data": citizen_id
            },
            table=table
        )

def get_form_template_by_id(form_template_id, table):
    pk = f"#F{form_template_id}#"
    sk = f"#F{form_template_id}#"
    return table.get_item(Key={'pk': pk, 'sk': sk})


def write_form_template(form_template_id, data, table):
    pk = f"#F{form_template_id}#"
    sk = f"#F{form_template_id}#"
    response = write_to_ddb(
        item={
            "pk": pk,
            "sk": sk,
            "data": data
        },
        table=table
    )
    print(response)
    return form_template_id

def write_form_template_field(form_template_id, field_id, data, table):
    pk = f"#F{form_template_id}#"
    sk = f"#F{form_template_id}#F{field_id}#"
    data = data
    response = write_to_ddb(
        item={
            "pk": pk,
            "sk": sk,
            "data": data
        },
        table=table
    )
    print(response)
    return response

def start_form_version(form_template_id, citizen_id, table):
    version_id = shortuuid.uuid()
    pk = f"#F{form_template_id}#"
    sk = f"#F{form_template_id}#{citizen_id}#{version_id}#"
    data = "STARTED"
    response = write_to_ddb(
        item={
            "pk": pk,
            "sk": sk,
            "data": data
        },
        table=table
    )
    print(response)
    return version_id

def submit_form_version(form_template_id, citizen_id, version_id, table):
    pk = f"#F{form_template_id}#"
    sk = f"#F{form_template_id}#C{citizen_id}#V{version_id}#"
    data = "SUBMITTED"
    return write_to_ddb(
        item={
            "pk": pk,
            "sk": sk,
            "data": data
        },
        table=table
    )

def write_form_field(form_template_id, citizen_id, version_id, field_id, data, table):
    pk = f"#F{form_template_id}#"
    sk = f"#F{form_template_id}#C{citizen_id}#V{version_id}#F{field_id}#" # todo - form ingestion should assign field_id's to fields in the form template
    return write_to_ddb(
        item={
            "pk": pk,
            "sk": sk,
            "data": data
        },
        table=table
    )

def get_form_fields_for_version(form_template_id, citizen_id, version_id, table):
    pk = f"#F{form_template_id}#"
    # sk = f"#F{form_template_id}#C{citizen_id}#V{version_id}#F{field_id}#" # todo - form ingestion should assign field_id's to fields in the form template
    fields = table.query(
        KeyConditionExpression=Key('pk').eq(pk) & Key('sk').begins_with(f"#F{form_template_id}#{citizen_id}#{version_id}")
    )
    return fields['Items']

def get_form_fields(form_template_id, citizen_id, table):
    pk = f"#F{form_template_id}#"
    # sk = f"#F{form_template_id}#V{version_id}#F{field_id}#" # todo - form ingestion should assign field_id's to fields in the form template
    fields = table.query(
        KeyConditionExpression=Key('pk').eq(pk) & Key('sk').begins_with(f"#F{form_template_id}#")
    )
    return fields['Items']
