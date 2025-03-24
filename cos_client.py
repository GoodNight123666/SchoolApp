from qcloud_cos import CosConfig, CosS3Client
import sys
import logging
from config import COS_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class COSClient:
    def __init__(self):
        self.client = None
    
    def get_client(self):
        if self.client is None:
            try:
                config = CosConfig(
                    Region=COS_CONFIG["region"],
                    SecretId=COS_CONFIG["secret_id"],
                    SecretKey=COS_CONFIG["secret_key"]
                )
                self.client = CosS3Client(config)
                logger.info("COS client initialized")
            except Exception as e:
                logger.error(f"COS client error: {str(e)}")
                raise e
        return self.client
    
    def get_file_list(self, prefix=""):
        """获取存储桶中的文件列表"""
        client = self.get_client()
        try:
            response = client.list_objects(
                Bucket=COS_CONFIG["bucket"],
                Prefix=prefix
            )
            
            files = []
            if "Contents" in response:
                for item in response["Contents"]:
                    files.append({
                        "key": item["Key"],
                        "last_modified": item["LastModified"],
                        "size": item["Size"],
                        "etag": item["ETag"]
                    })
            logger.info(f"Retrieved {len(files)} files from COS")
            return files
        except Exception as e:
            logger.error(f"Error getting file list: {str(e)}")
            raise e
    
    def get_presigned_url(self, key, expires=3600):
        """获取预签名临时下载URL"""
        client = self.get_client()
        try:
            # 使用正确的参数名称: Expired
            url = client.get_presigned_url(
                Method='GET',
                Bucket=COS_CONFIG["bucket"],
                Key=key,
                Expired=expires
            )
            logger.info(f"Generated presigned URL for {key}")
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise e

# 创建共享实例
cos_client = COSClient()