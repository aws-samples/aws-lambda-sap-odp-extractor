#!/bin/bash

# ======= Change these values [Required] ======= #
: ${SAPUser:=}          # User ID used to access SAP application
: ${BucketForSAMApp:=}  # Bucket where this SAM app is stored
# ======= Change these values [OPTIONAL] ======= #
: ${Environment:=saponaws-odp}       # Name will be added to all resources created
: ${DynamoDBTableName:="sap-odp-extract-metadata"}
: ${SAPAuthParameterStore:="sap-odp-extract-auth"}
: ${S3BucketForData:="sap-odp-data-extracts"}
: ${Region:=us-east-1}          # Region where resources will be deployed

# ======= Donot Change anything below this line ======= #
cr=`echo $'\n.'`
cr=${cr%.}
: ${SAPPassword:=}        

if [ -z "$SAPUser" ]
then
    read -s "Enter SAP User ID: \n" SAPUser
fi

if [ -z "$SAPPassword" ]
then
    read -s -p "Enter SAP Password: $cr" SAPPassword
    read -s -p "Re-enter SAP Password: $cr" SAPPassword1
    while [ "$SAPPassword" != "$SAPPassword1" ]; do 
        read -s -p "Password didn't match, enter again: $cr" SAPPassword1
    done
fi
    
Account=$(aws sts get-caller-identity --output text --query 'Account')

# Create bucket for storing the certs
S3BucketForData=$Account-$Region-$Environment-$S3BucketForData 

SAPAuthParameterStore=$Environment-$SAPAuthParameterStore

aws ssm put-parameter \
    --name $SAPAuthParameterStore \
    --description "Parameter to store SAP auth information" \
    --value "{\"user\":\"$SAPUser\",\"password\":\"$SAPPassword\"}" \
    --type "SecureString" \
    --overwrite \

aws s3 mb s3://$S3BucketForData --region $Region

# Deploy the app
sam package \
    --output-template-file packaged.yaml \
    --s3-bucket $BucketForSAMApp

aws cloudformation deploy \
    --template-file packaged.yaml \
    --stack-name $Environment \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
    Environment=$Environment \
    SAPAuthParameterStore=$SAPAuthParameterStore \
    S3BucketForData=$S3BucketForData  \
    DynamoDBTableName=$DynamoDBTableName
    