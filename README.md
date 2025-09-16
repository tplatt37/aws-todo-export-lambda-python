# Todo Export Lambda Function

A simple AWS Lambda function that exports DynamoDB table data to CSV and provides a download link via SNS.


Generated with AWS Q Developer.

## How it works

1. **SQS Trigger**: Function is triggered by messages in an SQS queue
2. **DynamoDB Scan**: Scans the entire TodoItems-Dev table (configurable)
3. **CSV Generation**: Creates CSV with all item attributes and headers
4. **S3 Upload**: Stores the CSV file in an S3 bucket
5. **Pre-signed URL**: Generates a 5-minute download link
6. **SNS Notification**: Sends the download link via SNS topic

## Deployment

```bash
# Build and deploy
sam build
sam deploy --guided

# You'll be prompted for:
# - DynamoDBTableName (default: TodoItems-Dev)
# - S3BucketName (your existing bucket)
# - SQSQueueArn (your existing queue ARN)
# - SNSTopicArn (your existing topic ARN)
```

## Environment Variables

- `DYNAMODB_TABLE`: DynamoDB table name to scan
- `S3_BUCKET`: S3 bucket for CSV storage
- `SNS_TOPIC`: SNS topic ARN for notifications

## Testing

Send a message to your SQS queue to trigger the function. The message content doesn't matter - any message will trigger the export process.

## Output

The function creates a timestamped CSV file (e.g., `todo_export_20231201_143022.csv`) and sends a download link via SNS that expires in 5 minutes.