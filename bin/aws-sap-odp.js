#!/usr/bin/env node
const cdk = require('@aws-cdk/core');
const { AwsSAPOdpStack } = require('../lib/aws-sap-odp-stack');
const AppConfig = require('../lib/appConfig.json') 

const app = new cdk.App();
const awsodpstack = new AwsSAPOdpStack(app, AppConfig.stackName, { env: AppConfig.env });
