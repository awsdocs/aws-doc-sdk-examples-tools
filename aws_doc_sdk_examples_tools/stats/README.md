
# CodeCommitCloneStack

Deploys an AWS Lambda function that monitors a CodeCommit repository for updates, extracts data from a `.stats` file, and appends it to a `stats.csv` file in an S3 bucket.

## Architecture

- **Lambda Function**: Pulls `.stats` file from CodeCommit, parses it, updates `stats.csv` in S3.
- **EventBridge Rule**: Triggers Lambda on CodeCommit repository changes.
- **IAM Role**: Grants Lambda necessary permissions for CodeCommit and S3 access.

## Prerequisites

- **Node.js**
- **AWS CDK**: `npm install -g aws-cdk`
- **AWS CLI**: Configured for your account
- **Python 3.9** (Lambda runtime)

## Deployment

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Deploy Stack**:
   ```bash
   cdk deploy
   ```

## Testing

Commit to the monitored CodeCommit repo and verify that `stats.csv` in S3 updates. Check Lambda logs in CloudWatch for details.

## Cleanup

```bash
cdk destroy
```

---

**License**: Apache-2.0
