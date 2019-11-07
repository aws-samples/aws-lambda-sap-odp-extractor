const cdk = require('@aws-cdk/core')
const iam = require('@aws-cdk/aws-iam')
const sm = require('@aws-cdk/aws-secretsmanager')
const s3 = require('@aws-cdk/aws-s3')
const dynamodb = require('@aws-cdk/aws-dynamodb')
const lambda = require('@aws-cdk/aws-lambda')
const AppConfig = require('./appConfig.json')
const path = require('path')

class AwsSAPOdpStack extends cdk.Stack {
    constructor(scope, id, props) {
        super(scope, id, props);

        //Lambda role
        const lambdaRole = new iam.Role(this, 'SAPLambdaRole', {assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com')})
        //Add basic execution
        lambdaRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AWSLambdaExecute'))
        
        //Create a secret manager secret
        const secret = new sm.Secret(this, 'SAPAuth',{
            generateSecretString: {
                secretStringTemplate: JSON.stringify({ user: 'SAPUserName' }),
                generateStringKey: 'password'
            }
        })
        secret.grantRead(lambdaRole)
        
        //DynamoDB for metadata
        const metadataTable = new dynamodb.Table(this,'metadatatable',{
            partitionKey: {
                name: 'odpServiceName',
                type: dynamodb.AttributeType.STRING
            },
            sortKey: {
                name: 'odpEntitySetName',
                type: dynamodb.AttributeType.STRING
            },
            removalPolicy: cdk.RemovalPolicy.DESTROY
        })
        metadataTable.grantReadWriteData(lambdaRole)
        
        //Bucket to store data
        const dataBucket = new s3.Bucket(this, 'databucket')
        dataBucket.grantReadWrite(lambdaRole)

        //Lambda Layer
        const extractorLayer = new lambda.LayerVersion(this, 'ExtractorLayer', {
            code: lambda.Code.fromAsset(path.join(__dirname, 'lambda/layers/aws-sap-odp-extractor')),
            compatibleRuntimes: [lambda.Runtime.PYTHON_2_7,lambda.Runtime.PYTHON_3_6,lambda.Runtime.PYTHON_3_7],
            license: 'Apache-2.0',
            description: 'Layer to dynamically generator user certificates for SAP user',
        })

        //Lambda function
        const extractorTestLambda = new lambda.Function(this,'TestLambdaFunction',{
            code: lambda.Code.fromAsset(path.join(__dirname, 'lambda/functions/aws-sap-odp-extractor-test')),
            runtime: lambda.Runtime.PYTHON_3_6,
            handler: 'main.lambda_handler',
            description: 'Sample Lambda function to for extracting from ODP',
            layers: [extractorLayer],
            role: lambdaRole,
            timeout: cdk.Duration.seconds(300),
            memorySize: 2048,
            environment: {
                sapHostName: "<your sap hostname> for e.g. mysaphost.com>",
                sapPort: "<your sap https port> for e.g. 44300",
                sapAuthSecret: secret.secretArn,
                metaDataDDBName: metadataTable.tableName,
                odpServiceName: "<your odata service name>",
                odpEntitySetName: "<your odp entity set name within the odata service>",
                dataChunkSize: "1000",
                dataS3Bucket: dataBucket.bucketName,
                dataS3Folder: "<Your Folder for storing the data to>"
            }
        })

        //Outputs
        new cdk.CfnOutput(this,'S3BucketForExtracts',{
            value: dataBucket.bucketName,
            description: "S3 bucket where extracted data will be stored",
            exportName: AppConfig.cfexports.S3BucketForExtracts
        })

        new cdk.CfnOutput(this,'DDBForMetaData',{
            value: metadataTable.tableName,
            description: "DynamoDB table where metadata will be stored",
            exportName: AppConfig.cfexports.DDBForMetaData
        })

        new cdk.CfnOutput(this,'SAPAuthSecret',{
            value: secret.secretArn,
            description: "Secret Name to store the SAP Auth data",
            exportName: AppConfig.cfexports.SAPAuthSecret
        })
    }
    
}

module.exports = {
    AwsSAPOdpStack
}