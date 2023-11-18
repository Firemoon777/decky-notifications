import asyncio
import base64
import logging
import os

from connector.const import LOCAL_PRIVATE_KEY_FILE, LOCAL_CERTIFICATE_FILE, LOCAL_PUBLIC_KEY_FILE


logger = logging.getLogger(__name__)


clear_env = os.environ
if "LD_LIBRARY_PATH" in clear_env:
    del clear_env["LD_LIBRARY_PATH"]


async def certificate_create(device_id: str):
    """
    Creates local self-signed certificate
    """
    device_id = device_id.replace("'", "")
    proc = await asyncio.create_subprocess_shell(
        "openssl req "
        "-x509 "
        "-newkey rsa:4096 "
        f"-keyout {LOCAL_PRIVATE_KEY_FILE} "
        f"-out {LOCAL_CERTIFICATE_FILE} "
        # f"-pubkey {LOCAL_PUBLIC_KEY_FILE} "
        "-sha256 "
        "-days 3650 "
        "-nodes "
        f"-subj '/C=US/O=KDE/OU=KDE Connect/CN={device_id}'",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=clear_env
    )

    ret = await proc.wait()
    if ret != 0:
        logger.error(f"certificate_create subprocess exited with code {ret}")
        logger.error("=== STDOUT ===")
        logger.error(f"{await proc.stdout.read()}")
        logger.error("=== STDERR ===")
        logger.error(f"{(await proc.stderr.read()).decode('866')}")
        logger.error("=== ENVIRON ===")
        for k, v in clear_env.items():
            logger.error(f"{k}: {v}")


async def certificate_get_public_key(cert: bytes, is_der: bool = True) -> bytes:
    """
    Compute public key by certificate
    """
    proc = await asyncio.create_subprocess_shell(
        "openssl x509 "
        "-pubkey " +
        ("-inform DER " if is_der else "") +
        f"-noout ",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=clear_env
    )

    stdout, stderr = await proc.communicate(cert)
    return get_der_by_pem(stdout)


def get_der_by_pem(in_: bytes):
    arr = in_.strip(b"\n").split(b"\n")
    # Drop ----BEGIN BLABLA---- and ----END BLABLA----
    key_encoded = b"".join(arr[1:-1])
    return base64.b64decode(key_encoded)
