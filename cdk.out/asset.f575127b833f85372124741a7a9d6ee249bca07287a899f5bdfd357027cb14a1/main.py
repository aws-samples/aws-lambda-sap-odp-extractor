import extractor
import boto3
import json
import os

def lambda_handler(event,context):
    # Get the SAP auth data
    sm = boto3.client('secretsmanager')
    secretResponse = sm.get_secret_value(SecretId=os.environ['sapAuthSecret'])
    sapauth = json.loads(secretResponse['SecretString'])
    
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