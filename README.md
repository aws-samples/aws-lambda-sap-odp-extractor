# aws-sap-cert-auth

This is a sample serverless application (based on AWS Serverless Application Model - AWS SAM) for extracting data from SAP applications (SAP S/4HANA, SAP ECC and SAP BW) using Operational Data Provisioning (ODP). You can find more information on ODP [here](https://blogs.sap.com/2017/07/20/operational-data-provisioning-odp-faq/). Operational Data Provisioning can expose the full load and delta data using OData services. This application package contains a Lambda layer to connect with SAP and consume the OData services as a REST API. Extracted data is saved to S3 Bucket. A DynamoDB table is also created to store the metadata for extracts. The package also contains a sample Lambda function to demonstrate usage of the lamdba layer

## Requirements

* [AWS CLI already configured with Administrator permission](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html)
* [NodeJS 8.10+ installed](https://nodejs.org/en/download/)
* [Docker installed](https://www.docker.com/community-edition)
* [AWS SAM CLI installed](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* SAP application (ABAP stack) with SAP Netweaver 7.5 or above. If required, you can create an SAP ABAP developer edition using cloud formation template [here](https://github.com/aws-samples/aws-cloudformation-sap-abap-dev)
* OData services for ODP based extraction are already created. It is assumed to you know about ODP and how OData services can be created from them. [This](https://www.google.com/search?q=sap+odp+odata&oq=sap+odp+odata&aqs=chrome..69i57j69i60j69i65j69i60l2j69i59.1812j0j7&sourceid=chrome&ie=UTF-8) SAP documentation link provides information on how to expose ODP as OData services. You can find more information on ODP [here](https://blogs.sap.com/2017/07/20/operational-data-provisioning-odp-faq/).

## Setup Process

### Installation

1. Clone this repo to a folder of your choice

2. Navigate to the root folder of the cloned repo and then perform the preparation steps.
```bash
cd aws-sap-odp
```

### Preparation

1. Create parameter store entry for storing the SAP user ID and password details. Make sure to change the value field with your user name and password
```bash
aws ssm put-parameter \
    --name sap-odp-extract-auth \
    --description "Parameter to store SAP auth information" \
    --value "{\"user\":\"MYUSERNAME\",\"password\":\"MYPASSWORD\"}" \
    --type "SecureString" \
    --overwrite \
```
2. Create S3 bucket where extracted data can be stored. Make sure to change the bucket name and your region as required.
```bash
aws s3 mb s3://sap-odp-data-extracts --region us-east-1
```

### Local Testing

**Invoking function locally using a local sample payload**

1. Create a file with name environment.json. Use the following format
```javascript
{
    "SAPODPExtractorTestFunction": {
        "sapHostName" :  "<your sap host name> for e.g. mysap.com (without https://)",
        "sapPort" :  "<your sap https port>",
        "sapAuthParameterStore": "<SSM Parameter created in step 1 above> for e.g. saponaws-odp-sap-odp-extract-auth",
        "metaDataDDBName" : "sap-odp-extract-metadata",
        "odpServiceName" : "<your ODP service name> for e.g. Z_ODP_EXTRACTORS_DEMO_SRV",
        "odpEntitySetName" : "<your ODP entity set name> for e.g. ZKK_SALES_ORDERS",
        "dataChunkSize" : "300",
        "dataS3Bucket": "<bucket creted in step 2 above> for e.g. saponaws-odp-sap-odp-data-extracts"
     }
}
```

2. Start the Lambda function locally. Note down the end point url where Lambda is running. Usually http://127.0.0.1:3001
```bash

sam local start-lambda \
    --env-vars environment.json \
    --template ../template.yaml \
    --parameter-overrides \
        'ParameterKey=Environment,ParameterValue=saponaws-odp ParameterKey=DynamoDBTableName ParameterValue=sap-odp-extract-metadata'
```

3. Open another terminal window and run the following command to invoke the lambda function. Validate the local endpoint url for Lambda
```bash

aws lambda invoke \
    --function-name "SAPODPExtractorTestFunction" \
    --endpoint-url "http://127.0.0.1:3001" \
    --no-verify-ssl \
    out.txt

```
4. Once run, check out.txt which should have the output of the lambda function

### Error Handling

In case of errors, check the values in the response body. 'success' will have a value of false. 'message' should provide you the reason for the failure and 'traceback' provides the stack trace of the exception. Go through the documentation of the extractor.py layer below to understand how the code works

## Deployment

1. Create a S3 bucket for storing latest version of your SAM app. If you are using an existing bucket, proceeed to step 2
```bash

aws s3 mb s3://<your account id>-sap-odp-extractor-sam-app>

```

2. Package the SAM app
```bash

sam package \
    --output-template-file packaged.yaml \
    --s3-bucket <<Your S3 bucket for SAM apps created above>>

```

3. Deploy the SAM app
```bash
aws cloudformation deploy \
    --template-file packaged.yaml \
    --stack-name saponaws-odp \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
    Environment=saponaws-odp \
    SAPAuthParameterStore="Parameter store name from perparation step 1" \
    S3BucketForData="Bucket name from perparation step 2"  \
    DynamoDBTableName=sap-odp-extract-metadata
```

## Cleanup

In order to delete our Serverless Application recently deployed you can use the following AWS CLI Command:
```bash
aws cloudformation delete-stack --stack-name saponaws-odp
```

