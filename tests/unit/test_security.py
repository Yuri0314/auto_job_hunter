"""
加密模块单元测试
"""

import pytest
from backend.core.security import SecretEncryption, encrypt_value, decrypt_value, is_encrypted


class TestSecretEncryption:
    """加密模块测试"""

    def test_encrypt_decrypt(self):
        """测试加密解密"""
        encryptor = SecretEncryption("test-secret-key")
        plaintext = "my-secret-password"
        ciphertext = encryptor.encrypt(plaintext)

        assert ciphertext != plaintext
        assert encryptor.decrypt(ciphertext) == plaintext

    def test_encrypt_empty_string(self):
        """测试空字符串加密"""
        encryptor = SecretEncryption("test-secret-key")
        assert encryptor.encrypt("") == ""
        assert encryptor.decrypt("") == ""

    def test_is_encrypted(self):
        """测试加密检测"""
        encryptor = SecretEncryption("test-secret-key")
        plaintext = "my-password"
        ciphertext = encryptor.encrypt(plaintext)

        assert encryptor.is_encrypted(ciphertext) is True
        assert encryptor.is_encrypted(plaintext) is False
        assert encryptor.is_encrypted("") is False

    def test_different_keys(self):
        """不同密钥不能解密"""
        encryptor1 = SecretEncryption("key-1")
        encryptor2 = SecretEncryption("key-2")

        plaintext = "secret"
        ciphertext = encryptor1.encrypt(plaintext)

        # 不同密钥应该无法解密
        with pytest.raises(Exception):
            encryptor2.decrypt(ciphertext)

    def test_global_functions(self):
        """测试全局函数"""
        plaintext = "test-value"
        ciphertext = encrypt_value(plaintext)

        assert is_encrypted(ciphertext) is True
        assert decrypt_value(ciphertext) == plaintext