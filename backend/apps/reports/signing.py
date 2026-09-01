"""Cryptographic PDF signing for generated certificates.

Signs certificates with an X.509 key pair so any later modification of the
PDF invalidates the signature (visible in Adobe Reader's signature panel).

The signing key is created on first use and stored under
REPORT_STORAGE_PATH/keys/. In production, mount a persistent key or provide
one issued by a CA; a self-signed certificate still provides tamper
evidence, it is simply not chained to a public trust root.
"""

import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

KEY_DIR_NAME = 'keys'
KEY_FILE = 'signing_key.pem'
CERT_FILE = 'signing_cert.pem'


def _key_paths() -> tuple[Path, Path]:
    key_dir = Path(settings.REPORT_STORAGE_PATH) / KEY_DIR_NAME
    key_dir.mkdir(parents=True, exist_ok=True)
    return key_dir / KEY_FILE, key_dir / CERT_FILE


def _ensure_signing_material() -> tuple[Path, Path]:
    """Create a self-signed signing certificate on first use."""
    key_path, cert_path = _key_paths()
    if key_path.exists() and cert_path.exists():
        return key_path, cert_path

    from datetime import datetime, timedelta, timezone

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, 'IN'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Legal Metrology Laboratory'),
        x509.NameAttribute(NameOID.COMMON_NAME, 'NAWI Test Report Generator'),
    ])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=True,
                key_encipherment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=False, crl_sign=False,
                encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    key_path.write_bytes(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    logger.info("Generated new PDF signing certificate at %s", cert_path)
    return key_path, cert_path


def sign_pdf(pdf_path: str, reason: str = 'Certificate issuance') -> bool:
    """Sign the PDF in place. Returns True on success, False otherwise.

    Never raises — an unsigned certificate is still delivered rather than
    failing report generation.
    """
    try:
        from pyhanko.sign import signers
        from pyhanko.sign.fields import SigFieldSpec, append_signature_field
        from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

        key_path, cert_path = _ensure_signing_material()
        signer = signers.SimpleSigner.load(
            str(key_path), str(cert_path), key_passphrase=None,
        )
        if signer is None:
            logger.error("Could not load PDF signing key material")
            return False

        path = Path(pdf_path)
        tmp_path = path.with_suffix('.signed.pdf')
        with open(path, 'rb') as inf:
            writer = IncrementalPdfFileWriter(inf)
            append_signature_field(
                writer, SigFieldSpec(sig_field_name='CertificateSignature'),
            )
            meta = signers.PdfSignatureMetadata(
                field_name='CertificateSignature',
                reason=reason,
                location='Legal Metrology Laboratory',
            )
            with open(tmp_path, 'wb') as outf:
                signers.sign_pdf(writer, meta, signer=signer, output=outf)
        tmp_path.replace(path)
        logger.info("PDF signed: %s", path)
        return True
    except Exception:
        logger.exception("PDF signing failed; certificate remains unsigned")
        return False
