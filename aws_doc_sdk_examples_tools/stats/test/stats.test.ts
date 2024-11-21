import * as cdk from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { CodeCommitCloneStack } from "../app";

describe("CodeCommitCloneStack", () => {
  const app = new cdk.App();
  const stack = new CodeCommitCloneStack(app, "TestCodeCommitCloneStack", {
    env: {
      account: "123456789012",
      region: "us-west-2",
    },
  });
  const template = Template.fromStack(stack);

  test("Lambda function created with correct properties", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      Handler: "index.lambda_handler",
      Runtime: "python3.9",
      Timeout: 300,
      Environment: {
        Variables: {
          REPO_NAME: "AWSDocsSdkExamplesPublic",
        },
      },
    });
  });

  test("EventBridge rule created with correct event pattern", () => {
    template.hasResourceProperties("AWS::Events::Rule", {
      EventPattern: {
        source: ["aws.codecommit"],
        "detail-type": ["CodeCommit Repository State Change"],
        resources: [
          `arn:aws:codecommit:us-west-2:123456789012:AWSDocsSdkExamplesPublic`,
        ],
        detail: {
          event: ["referenceCreated", "referenceUpdated", "referenceDeleted"],
        },
      },
    });
  });

  test("Lambda function added as a target for the EventBridge rule", () => {
    template.hasResourceProperties("AWS::Events::Rule", {
      Targets: [
        Match.objectLike({
          Arn: { "Fn::GetAtt": [Match.anyValue(), "Arn"] },
          Id: "Target0",
        }),
      ],
    });
  });
});
