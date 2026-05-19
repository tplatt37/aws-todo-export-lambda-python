import json
import csv
import boto3
import os
from datetime import datetime
from io import StringIO
from botocore.config import Config

def lambda_handler(event, context):
    # Initialize AWS clients
    dynamodb = boto3.resource('dynamodb')
    # Must do the following to ensure regions other than us-east-1 work when presigning
    s3 = boto3.client(
        's3',
        region_name=os.environ['AWS_REGION'],
        endpoint_url=f"https://s3.{os.environ['AWS_REGION']}.amazonaws.com",
        config=Config(signature_version='s3v4')
    )
    sns = boto3.client('sns')
    
    # Get environment variables
    table_name = os.environ['DYNAMODB_TABLE_NAME']
    bucket_name = os.environ['S3_BUCKET_NAME']
    sns_topic = os.environ['SNS_TOPIC_ARN']
    
    try:
        # Scan DynamoDB table
        table = dynamodb.Table(table_name)
        response = table.scan()
        items = response['Items']
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
        
        print(f"Found {len(items)} items in DynamoDB table")
        
        # Generate CSV
        if not items:
            print("No items found in table")
            return {'statusCode': 200, 'body': 'No items to export'}
        
        # Get all unique keys for CSV headers
        all_keys = set()
        for item in items:
            all_keys.update(item.keys())
        headers = sorted(list(all_keys))
        
        # Create CSV content
        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=headers)
        writer.writeheader()
        writer.writerows(items)
        csv_content = csv_buffer.getvalue()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"todo_export_{timestamp}.csv"
        
        # Upload to S3
        s3.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=csv_content,
            ContentType='text/csv'
        )
        print(f"Uploaded {filename} to S3 bucket {bucket_name}")
        
        # Generate pre-signed URL (5 minutes = 300 seconds)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': filename},
            ExpiresIn=300
        )
        
        # Send SNS notification
        message = f"Todo export completed! Download your CSV file here: {presigned_url}"
        sns.publish(
            TopicArn=sns_topic,
            Message=message,
            Subject="Todo Export Ready for Download"
        )
        print("SNS notification sent")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Export completed successfully',
                'filename': filename,
                'items_exported': len(items)
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }