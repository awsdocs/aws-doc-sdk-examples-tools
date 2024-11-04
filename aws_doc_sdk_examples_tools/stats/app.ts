// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as iam from "aws-cdk-lib/aws-iam";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import { Construct } from "constructs";
import * as path from "path";

const repoName = "AWSDocsSdkExamplesPublic";
const awsRegion = "us-west-2";

class CodeCommitCloneStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create Lambda function
    const cloneLambda = this.initCloneLambda();

    // Create EventBridge rule to trigger Lambda on CodeCommit repository changes
    this.initCodeCommitTrigger(cloneLambda);
  }

  private initCloneLambda(): lambda.Function {
    // IAM Role and Policy for Lambda to access CodeCommit
    const lambdaExecutionRole = new iam.Role(this, "CloneLambdaExecutionRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      description: "Execution role for Lambda function to clone CodeCommit repo",
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName("service-role/AWSLambdaBasicExecutionRole"),
      ],
    });

    // Grant necessary permissions to CodeCommit and S3
    lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "codecommit:GetRepository",
          "codecommit:GitPull",
          "codecommit:GetBranch",
          "codecommit:GetDifferences",
          "codecommit:GetFile"
        ],
        resources: [`arn:aws:codecommit:${awsRegion}:${this.account}:${repoName}`],
      })
    );

    // Grant necessary permissions to S3 bucket "codeexamplestats" for Get/Put
    lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["s3:GetObject", "s3:PutObject"],
        resources: [`arn:aws:s3:::codeexamplestats/*`],  // Allow all objects in the bucket
      })
    );

    // Define the Lambda function, pointing directly to the source code dir
    const cloneLambda = new lambda.Function(this, "CodeCommitCloneLambda", {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: "index.lambda_handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "lambda")),
      environment: {
        REPO_NAME: repoName,
      },
      timeout: cdk.Duration.minutes(5),
      role: lambdaExecutionRole,
    });

    return cloneLambda;
  }

  private initCodeCommitTrigger(cloneLambda: lambda.Function): void {
    // EventBridge rule for CodeCommit repo updates
    const codeCommitRule = new events.Rule(this, "CodeCommitUpdateRule", {
      eventPattern: {
        source: ["aws.codecommit"],
        detailType: ["CodeCommit Repository State Change"],
        resources: [`arn:aws:codecommit:${awsRegion}:${this.account}:${repoName}`],
        detail: {
          event: [
            "referenceCreated",
            "referenceUpdated",
            "referenceDeleted"
          ]
        }
      }
    });

    // Add Lambda function as target of the EventBridge rule
    codeCommitRule.addTarget(new targets.LambdaFunction(cloneLambda));
  }
}

const app = new cdk.App();
new CodeCommitCloneStack(app, "CodeCommitCloneStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: "us-west-2",  // Where codecommit is stored (internal requirement)
  },
});
app.synth();
