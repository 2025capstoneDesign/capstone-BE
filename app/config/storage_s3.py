import boto3
from app.config.settings import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

def upload_file_to_s3(file_obj, filename: str, content_type: str) -> str:
    bucket = settings.AWS_S3_BUCKET
    s3_client.upload_fileobj(
        Fileobj=file_obj,
        Bucket=bucket,
        Key=filename,
        ExtraArgs={"ContentType": content_type}
    )
    url = f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
    return url