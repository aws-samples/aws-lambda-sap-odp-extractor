# aws-lambda-sap-odp-extractor

> :warning: Note: This content is outdated, consider using [Amazon AppFlow for SAP](https://catalog.workshops.aws/sap-on-aws-beyond/en-US/aws-datalakes-for-sap/application-level/2-9-sap-appflow) instead!

This is a sample application for extracting data from SAP applications (SAP S/4HANA, SAP ECC and SAP BW) using Operational Data Provisioning (ODP). You can find more information on ODP [here](https://blogs.sap.com/2017/07/20/operational-data-provisioning-odp-faq/). Operational Data Provisioning can expose the full load and delta data using OData services. This application package contains a Lambda layer to connect with SAP and consume the OData services as a REST API. Extracted data is saved to S3 Bucket. A DynamoDB table is also created to store the metadata for extracts. The package also contains a sample Lambda function to demonstrate usage of the lamdba layer

## Requirements

* [AWS CLI already configured with Administrator permission](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html)
* [NodeJS 10.x installed](https://nodejs.org/en/download/)
* [AWS CDK installed](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html)
* SAP application (ABAP stack) with SAP Netweaver 7.5 or above. If required, you can create an SAP ABAP developer edition using cloud formation template [here](https://github.com/aws-samples/aws-cloudformation-sap-abap-dev)
* OData services for ODP based extraction are already created. It is assumed to you know about ODP and how OData services can be created from them. [This](https://help.sap.com/viewer/ccc9cdbdc6cd4eceaf1e5485b1bf8f4b/7.5.9/en-US/11853413cf124dde91925284133c007d.html) SAP documentation link provides information on how to expose ODP as OData services. You can find more information on ODP [here](https://blogs.sap.com/2017/07/20/operational-data-provisioning-odp-faq/).

## Setup Process

Note: This process creates various resources in your AWS account. Check the resources created section for more information what gets created. You incur charges for using the resources created and you are responsible for those charges.

### Installation

1. Clone this repo to a folder of your choice

2. Navigate to the root folder of the cloned repo and then perform the preparation steps.
```bash
cd aws-lambda-sap-odp-extractor
npm install
```
3. Navigate to the lib folder
```bash
cd lib
```
4. Update the appConfig.json file in the lib folder to suit your needs. At a minimum, update your account ID, region details.

5. Navigate to project root folder
```bash
cd ..
```

6. Bootstrap your AWS account for CDK. Please check [here](https://docs.aws.amazon.com/cdk/latest/guide/tools.html) for more details on bootstraping for CDK. Bootstraping deploys a CDK toolkit stack to your account and creates a S3 bucket for storing various artifacts. You incur any charges for what the AWS CDK stores in the bucket. Because the AWS CDK does not remove any objects from the bucket, the bucket can accumulate objects as you use the AWS CDK. You can get rid of the bucket by deleting the CDKToolkit stack from your account.
```bash
cdk bootstrap aws://<YOUR ACCOUNT ID>/<YOUR AWS REGION>
```

7. Deploy the stack to your account. Make sure your CLI is setup for account ID and region provided in the appConfig.json file. 
```bash
cdk deploy
```
8. Once the stack is deployed successfully, go to Secrets Manager and update the SAP user ID and password for connecting to the backend SAP application and pull data using OData/ODP. You can get the secrets manager ARN from the output of the CDK output or CloudFormation output

### Testing

1. Open test Lambda function (you can get the name from the CloudFormation output) and update the dataS3Folder, odpServiceName, odpEntitySetName, sapHostName and sapPort according to your SAP application and OData details

2. Execute a test in the Lambda function. This should extract the data from backend SAP application and load it to the S3 bucket.

## Cleanup

In order to delete all resources created by this CDK app, run the following command
```bash
cdk destroy
```

