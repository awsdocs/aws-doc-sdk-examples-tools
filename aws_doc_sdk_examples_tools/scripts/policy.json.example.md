# Example output of the snippet_summarize script for IAM policies
```
[
  {
    "title": "Allows Amazon SNS to send messages to an Amazon SQS dead-letter queue",
    "title_abbrev": "Allows SNS to SQS messages",
    "description": "This resource-based policy allows Amazon SNS to send messages to a specific Amazon SQS dead-letter queue. The policy grants the SNS service principal permission to perform the SQS:SendMessage action on the queue named [MyDeadLetterQueue], but only when the source ARN matches the specified SNS topic [MyTopic]. This policy would be attached to the SQS queue to enable it to receive messages from the SNS topic when message delivery fails. Replace [us-east-2] with your specific AWS Region."
  },
  {
    "title": "Allows managing log delivery and related resources",
    "title_abbrev": "Allows log delivery management",
    "description": "This identity-based policy allows managing CloudWatch Logs delivery configurations and related resources. The policy grants permissions to create, get, update, delete, and list log deliveries, as well as manage resource policies for a specific log group [SampleLogGroupName]. It also allows creating service-linked roles, tagging Firehose delivery streams, and managing bucket policies for a specific S3 bucket [bucket-name]. Replace [region] and [account-id] with your specific AWS Region and account ID, and [bucket-name] with your actual S3 bucket name."
  },
  {
    "title": "Allows Amazon SNS to send messages to an SQS dead-letter queue",
    "title_abbrev": "SNS to SQS permissions",
    "description": "This resource-based policy allows Amazon SNS to send messages to a specific Amazon SQS queue that serves as a dead-letter queue. The policy grants the SNS service permission to perform the SQS:SendMessage action on the queue named [MyDeadLetterQueue] in the [us-east-2] Region. The policy includes a condition that restricts this permission to messages originating from the SNS topic named [MyTopic] in the same Region and account."
  }
]
```