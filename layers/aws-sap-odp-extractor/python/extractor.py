# ------------------------
# All Imports
# ------------------------
import boto3
import requests
from requests.auth import HTTPBasicAuth
import json
import os
import traceback
import copy
import uuid

# ------------------------
# Globals
# ------------------------
sapHostName = ""
sapPort = ""
sapUser = ""
sapPassword = ""
odpServiceName = ""
odpEntitySetName = ""
dataChunkSize = "1000"
metaDataDDBName = ""
dataS3Bucket = ""
selfSignedCertificate = ""
selfSignedCertificateS3Bucket = ""
selfSignedCertificateS3Key = ""
reLoad = False
_athenacompatiblejson = False
_allowInValidCerts = False

# ------------------------
# All Constants
# ------------------------
INITLOADING = "InitLoading"
INITLOADED = "InitLoaded"
DELTALOADING = "DeltaLoading"
DELTATOKEN = "!deltatoken="

# ------------------------
# Initialize
# ------------------------
def _setResponse(success,message, data, numberofrecs):
    response = {
        'success'   : success,
        'message'   : message,
        'traceback' : traceback.format_exc(),
        'data'      : data,
        'numberofrecs' : numberofrecs
    }
    return response

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(metaDataDDBName)
response = _setResponse(False,"Error in fetching data from SAP. Check detailed logs",None,0)

# ------------------------
# Main Extract entry point
# ------------------------
def extract():
    global response
    try:
        if reLoad == True:
            _extract(" ",True)
        else:
            metadata = _get_metadata()
            if metadata is None:
                _extract(" ",True)
            else:
                status = metadata.pop('status', " ")
                if status == INITLOADED or status == DELTALOADING:
                    _extract(metadata.pop('delta'," "),False)
                else:    
                    _extract(metadata.pop('next'," "),True)
    except Exception as e:
        response = _setResponse(False,str(e),None,0)

    return response    


# ------------------------
# Perform extract
# ------------------------
def _extract(link,isInit):
    global response
    url = link
    if url == " ":
        #url = _get_base_url() + "/EntityOf" + odpEntitySetName + "?$format=json"
        url = _get_base_url() + "/" + odpEntitySetName + "?$format=json"
    
    headers = {
        "prefer" : "odata.maxpagesize=" + dataChunkSize + ",odata.track-changes"
    }
    sapresponse =  _make_http_call_to_sap(url,headers)
    sapresponsebody = json.loads(sapresponse.text)
    _response = copy.deepcopy(sapresponsebody)

    d = sapresponsebody.pop('d',None)
    results = d.pop('results',None)
    for result in results:
        _metadata = result.pop('__metadata',None)
    
    if isInit == True:
        next = d.pop('__next'," ")
        if next == " ":
            _modify_ddb_table(INITLOADED,next,_get_delta_link())
        else:
            _modify_ddb_table(INITLOADING,next," ")
    else:
        delta = d.pop('__delta', " ")
        deltaTokenIndex = delta.find(DELTATOKEN)
        deltaLink = ""
        if deltaTokenIndex > -1:
            deltaToken = delta[deltaTokenIndex:len(delta)]
            deltaToken = deltaToken.replace(DELTATOKEN, "")
            deltaLink = _get_base_url() + "/DeltaLinksOf" + odpEntitySetName + "(" + deltaToken + ")/ChangesAfter?$format=json"
        else:
            deltaLink = _get_delta_link()

        _modify_ddb_table(DELTALOADING," ",deltaLink)
    
    if len(results)<=0:
        response = _setResponse(True,"No data available to extract from SAP", _response, 0)
    elif(dataS3Bucket != ""):
        s3 = boto3.resource('s3')
        fileName = ''.join([str(uuid.uuid4().hex[:6]),odpServiceName, "_", odpEntitySetName,".json"]) 
        object = s3.Object(dataS3Bucket, fileName)
        if _athenacompatiblejson==True:
            object.put(Body=_athenaJson(results))
        else:    
            object.put(Body=json.dumps(results,indent=4))
            
        response = _setResponse(True,"Data successfully extracted and stored in S3 Bucket with key " + fileName, None, len(results))
    else:
        response = _setResponse(True,"Data successfully extracted from SAP", _response, len(results))

# ------------------------------------
# Conver JSON to athena format
# ------------------------------------
def _athenaJson(objects):
    return '\n'.join(json.dumps(obj) for obj in objects)

# ------------------------------------
# Get base url for HTTP calls to SAP
# ------------------------------------
def _get_base_url():
    global sapPort
    if sapPort == "":
        sapPort = "443"
    return "https://" + sapHostName + ":" + sapPort + "/sap/opu/odata/SAP/" + odpServiceName

# ------------------------------------
# Get the last available delta link
# ------------------------------------    
def _get_delta_link():
    try:
        url = _get_base_url() + "/DeltaLinksOf" + odpEntitySetName + "?$format=json"
        sapresponse =  _make_http_call_to_sap(url,None)
        sapresponsebody = json.loads(sapresponse.text)
        d = sapresponsebody.pop('d',None)
        results = d.pop('results',None)
        if len(results) > 0:
            result = results[len(results)-1]
        
        changesAfter = result.pop('ChangesAfter',None)
        deferred = changesAfter.pop('__deferred',None)
        deltauri = deferred.pop('uri'," ")
        if deltauri != " ":
            deltauri = deltauri + "?$format=json"
        return deltauri
    except:
        return " "
    
# ------------------------------------
# Call SAP HTTP endpoint
# ------------------------------------    
def _make_http_call_to_sap(url,headers):
    #global selfSignedCertificate
    certFileName = os.path.join('/tmp/','sapcert.crt')
    verify = True
    if selfSignedCertificate != "" :
        certfile = open(certFileName,'w')
        os.write(certfile,selfSignedCertificate)
        verify = certFileName
    elif selfSignedCertificateS3Bucket != "" :
        s3 = boto3.client('s3')
        verify = certFileName
        with open(certFileName, 'w') as f:
            s3.download_fileobj(selfSignedCertificateS3Bucket, selfSignedCertificateS3Key, f)
        certfile = open(certFileName,'r')
        print(certfile.read())
    elif _allowInValidCerts == True:
        verify = False
    return requests.get( url,auth=HTTPBasicAuth(sapUser,sapPassword), headers=headers,verify=verify)


# ------------------------------------
# Get metadata from DynamoDB
# ------------------------------------    
def _get_metadata():

    ddbresponse = table.get_item(
        TableName=metaDataDDBName,
        Key={
            'odpServiceName': odpServiceName,
            'odpEntitySetName': odpEntitySetName
        }
    )
    if 'Item' in ddbresponse:
        return ddbresponse['Item']
    else:
        return None

# ------------------------------------
# Insert/Update records in DynamoDB
# ------------------------------------    
def _modify_ddb_table(status,next,delta):
    table.put_item(
        TableName=metaDataDDBName,
        Item={
                'odpServiceName': odpServiceName,
                'odpEntitySetName': odpEntitySetName,
                'status' : status,
                'next' : next,
                'delta' : delta,
        }
    )

