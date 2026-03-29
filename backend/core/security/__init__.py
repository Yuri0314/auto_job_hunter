"""
敏感数据加密模块

使用 Fernet 对称加密保护数据库中存储的敏感配置
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from loguru import logger


class SecretEncryption:
    """敏感数据加密器"""

    def __init__(self, secret_key: Optional[str] = None):
        """
        初始化加密器

        Args:
            secret_key: 加密密钥，如果未提供则从环境变量 SECRET_KEY 获取
        """
        self._secret_key = secret_key or os.environ.get("SECRET_KEY", "default-secret-key-change-in-production")
        self._fernet = self._derive_fernet_key()

    def _derive_fernet_key(self) -> Fernet:
        """从密钥派生 Fernet 密钥"""
        # 使用 PBKDF2 派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"auto_job_hunter_salt",  # 固定盐值，确保相同密钥产生相同加密结果
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._secret_key.encode()))
        return Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """
        加密文本

        Args:
            plaintext: 明文

        Returns:
            加密后的字符串（Base64 编码）
        """
        if not plaintext:
            return ""

        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        解密文本

        Args:
            ciphertext: 密文

        Returns:
            解密后的明文
        """
        if not ciphertext:
            return ""

        try:
            decrypted = self._fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def is_encrypted(self, value: str) -> bool:
        """
        检查值是否已被加密

        Args:
            value: 要检查的值

        Returns:
            是否为加密值
        """
        if not value:
            return False

        try:
            # 尝试解密，如果成功则说明是加密值
            self._fernet.decrypt(value.encode())
            return True
        except Exception:
            return False


# 全局加密器实例
_encryptor: Optional[SecretEncryption] = None


def get_encryptor() -> SecretEncryption:
    """获取加密器实例"""
    global _encryptor
    if _encryptor is None:
        _encryptor = SecretEncryption()
    return _encryptor


def encrypt_value(value: str) -> str:
    """加密值"""
    return get_encryptor().encrypt(value)


def decrypt_value(value: str) -> str:
    """解密值"""
    return get_encryptor().decrypt(value)


def is_encrypted(value: str) -> bool:
    """检查值是否已加密"""
    return get_encryptor().is_encrypted(value)