import extractor
import boto3
import json
import os

def lambda_handler(event,context):
    # Get the SAP auth data
    ssm = boto3.client('ssm')
    sapauth = json.loads(ssm.get_parameter(Name=os.environ['sapAuthParameterStore'], WithDecryption=True)['Parameter']['Value'])
    
    extractor.sapHostName = os.environ['sapHostName']
    extractor.sapPort = os.environ['sapPort']
    extractor.sapUser = sapauth['user']
    extractor.sapPassword = sapauth['password']
    extractor.metaDataDDBName = os.environ['metaDataDDBName']
    extractor.odpServiceName = os.environ['odpServiceName']
    extractor.odpEntitySetName = os.environ['odpEntitySetName']
    extractor.dataChunkSize = os.environ['dataChunkSize']
    extractor.dataS3Bucket = os.environ['dataS3Bucket']
    extractor._allowInValidCerts = True     ## Don't ever do this in production
    extractor._athenacompatiblejson = True
    return{
        'statusCode': 200,
        'body': extractor.extract()
    }