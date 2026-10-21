import base64

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def main() -> None:
    vapid = Vapid()
    vapid.generate_keys()
    private = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
    public = vapid.public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    print(f"VINI_VAPID_PUBLIC_KEY={_b64(public)}")
    print(f"VINI_VAPID_PRIVATE_KEY={_b64(private)}")


if __name__ == "__main__":
    main()
