# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import cfnresponse
import os
import time

from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

print("Setting up auth")
region = os.environ['AWS_REGION']
service = 'aoss'
credentials = boto3.Session().get_credentials()
awsauth = AWSV4SignerAuth(credentials, region, service)


def lambda_handler(event, context):
    print("Adding index")
    print(event)
    action = event['RequestType']
    props = event['ResourceProperties']
    os_url = props['os_url']
    index_name = props['index_name']
    print(f"{action} {index_name} on {os_url}")

    host = os_url.replace("https://", "")

    print(f"using hostname: {host}")

    print(f"Connecting to opensearch at {os_url}")

    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_compress=True,  # enables gzip compression for request bodies
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    print("got connection")

    index_settings = {
        "settings": {
            "index.knn": "true"
        },
        "mappings": {
            "properties": {
                "vector": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {
                        "name": "hnsw",
                        "engine": "faiss",
                        "space_type": "innerproduct",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        },
                    },
                },
                "text": {
                    "type": "text"
                },
                "text-metadata": {
                    "type": "text"
                }
            }
        }
    }

    try:
        if action == "Create":
            response = client.indices.create(
                index=index_name,
                body=json.dumps(index_settings)
            )
            time.sleep(60)
        elif action == "Delete":
            response = client.indices.delete(
                index=index_name,
            )
        event['response'] = response
    except Exception as err:
        print(err)
        cfnresponse.send(event, context, cfnresponse.FAILED, "FAILED", f"oas_index_{index_name}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Index create command failed'})
        }

    print(response)
    # it can take a minute for the index to be ready
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response, f"oas_index_{index_name}")
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }