"""
AWS Client Factory with proper retry configuration
"""
import boto3
from botocore.config import Config
from typing import Dict, Any, Optional


class AWSClientFactory:
    """Factory for creating AWS clients with appropriate retry configurations"""
    
    def __init__(self):
        self._sessions = {}
        
        # Default configuration for most operations
        self.default_config = Config(
            retries={
                'max_attempts': 10,
                'mode': 'adaptive'
            },
            max_pool_connections=50
        )
        
        # Configuration for quota operations (higher retry count due to throttling)
        self.quota_config = Config(
            retries={
                'max_attempts': 15,
                'mode': 'adaptive'
            },
            max_pool_connections=50
        )
        
        # Configuration for EC2 describe operations (lower retry count)
        self.ec2_config = Config(
            retries={
                'max_attempts': 5,
                'mode': 'standard'
            },
            max_pool_connections=50
        )
    
    def get_client(self, service: str, region: str, config: Optional[Config] = None) -> Any:
        """
        Get AWS client with built-in retry configuration
        
        Args:
            service: AWS service name (e.g., 'ec2', 'service-quotas')
            region: AWS region name
            config: Optional custom config, uses default if not provided
            
        Returns:
            Configured boto3 client
        """
        session_key = region
        if session_key not in self._sessions:
            self._sessions[session_key] = boto3.Session(region_name=region)
        
        client_config = config or self.default_config
        return self._sessions[session_key].client(service, config=client_config)
    
    def get_quota_client(self, region: str) -> Any:
        """Get service-quotas client optimized for quota operations"""
        return self.get_client('service-quotas', region, self.quota_config)
    
    def get_ec2_client(self, region: str) -> Any:
        """Get EC2 client optimized for describe operations"""
        return self.get_client('ec2', region, self.ec2_config)
    
    def get_rds_client(self, region: str) -> Any:
        """Get RDS client with default configuration"""
        return self.get_client('rds', region, self.default_config)


# Global factory instance
aws_client_factory = AWSClientFactory()