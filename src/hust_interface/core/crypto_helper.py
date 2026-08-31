import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TimetableCryptoHelper:
    """
    AES-CBC helper matching eHUST frontend encryption:
    - Key = SHA256("304c7f6dff373663d32879ac1c1f1318")
    - IV = MD5("069635c0806598e069583aee5440e448")
    """
    KEY_SEED = "304c7f6dff373663d32879ac1c1f1318"
    IV_SEED = "069635c0806598e069583aee5440e448"

    @classmethod
    def encrypt_payload(cls, data: Dict[str, Any]) -> str:
        import hashlib
        from urllib.parse import quote
        from Cryptodome.Cipher import AES
        from Cryptodome.Util.Padding import pad

        key = hashlib.sha256(cls.KEY_SEED.encode("utf-8")).digest()
        iv = hashlib.md5(cls.IV_SEED.encode("utf-8")).digest()

        raw_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")
        padded = pad(raw_bytes, AES.block_size, style="pkcs7")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_bytes = cipher.encrypt(padded)

        import base64
        b64 = base64.b64encode(encrypted_bytes).decode("utf-8")
        return quote(b64, safe="")

    @classmethod
    def decrypt_payload(cls, encrypted_b64_or_url: str) -> Dict[str, Any]:
        import hashlib
        import base64
        from urllib.parse import unquote
        from Cryptodome.Cipher import AES
        from Cryptodome.Util.Padding import unpad

        key = hashlib.sha256(cls.KEY_SEED.encode("utf-8")).digest()
        iv = hashlib.md5(cls.IV_SEED.encode("utf-8")).digest()

        raw_b64 = unquote(encrypted_b64_or_url)
        encrypted_bytes = base64.b64decode(raw_b64)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(encrypted_bytes)
        decrypted_bytes = unpad(decrypted_padded, AES.block_size, style="pkcs7")
        return json.loads(decrypted_bytes.decode("utf-8"))
