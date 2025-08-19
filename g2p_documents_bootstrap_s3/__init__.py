import logging
import os

_logger = logging.getLogger(__name__)

S3_URL = os.getenv("S3_URL")
S3_REGION = os.getenv("S3_REGION", "other")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")

S3_BUCKET_NAME_DOCUMENTS = os.getenv("S3_BUCKET_NAME_DOCUMENTS", "documents")
S3_BUCKET_NAME_PHOTOS = os.getenv("S3_BUCKET_NAME_PHOTOS", "photos")

S3_VIRUS_SCAN_URL = os.getenv("S3_VIRUS_SCAN_URL")
S3_PROFILE_PHOTOS_ENABLED = "false" != os.getenv("S3_PROFILE_PHOTOS_ENABLED")


def post_init_hook(env):
    env.ref("storage_backend.default_storage_backend").write(
        {
            "name": "Default S3 Document Store",
            "is_public": True,
            "backend_type": "amazon_s3",
            "aws_host": S3_URL,
            "aws_region": S3_REGION,
            "aws_access_key_id": S3_ACCESS_KEY_ID,
            "aws_secret_access_key": S3_SECRET_ACCESS_KEY,
            "aws_cache_control": "max-age=31536000, public",
            "aws_bucket": S3_BUCKET_NAME_DOCUMENTS,
            "mimetype_strategy": "from_data",
            "virus_scan_url": S3_VIRUS_SCAN_URL,
        }
    )

    if S3_PROFILE_PHOTOS_ENABLED:
        photos_store = env["storage.backend"].create(
            {
                "name": "Photos Document Store",
                "backend_type": "filesystem",
            }
        )

        # A direct create is not working properly. Hence have to create and update seperately.
        env.cr.commit()
        photos_store.write(
            {
                "backend_type": "amazon_s3",
                "is_public": True,
                "aws_host": S3_URL,
                "aws_region": S3_REGION,
                "aws_access_key_id": S3_ACCESS_KEY_ID,
                "aws_secret_access_key": S3_SECRET_ACCESS_KEY,
                "aws_cache_control": "max-age=31536000, public",
                "aws_bucket": S3_BUCKET_NAME_PHOTOS,
                "mimetype_strategy": "from_data",
                "virus_scan_url": S3_VIRUS_SCAN_URL,
            }
        )

        env["ir.config_parameter"].set_param(
            "g2p_profile_image.image_document_storage",
            str(photos_store.id),
        )
