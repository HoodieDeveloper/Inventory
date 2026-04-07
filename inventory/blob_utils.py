import os
from pathlib import Path
from uuid import uuid4

from django.core.files.storage import default_storage
from django.utils.text import slugify

from .models import Product

try:
    from vercel.blob import BlobClient, delete as delete_blob
    from vercel.blob.errors import BlobError
except Exception:  # pragma: no cover
    BlobClient = None
    BlobError = Exception
    delete_blob = None


class ProductImageUploadError(Exception):
    pass


def _safe_filename(filename: str) -> str:
    path = Path(filename)
    stem = slugify(path.stem) or 'image'
    suffix = path.suffix.lower() or '.jpg'
    return f"{stem}{suffix}"


def _blob_path(product_name: str, filename: str) -> str:
    product_slug = slugify(product_name) or 'product'
    return f"products/{product_slug}-{uuid4().hex[:8]}-{_safe_filename(filename)}"


def upload_product_image(uploaded_file, product_name: str) -> tuple[str, str]:
    if not uploaded_file:
        return '', ''

    token = os.getenv('BLOB_READ_WRITE_TOKEN')
    if token:
        if BlobClient is None:
            raise ProductImageUploadError('The Vercel Blob SDK is not installed correctly.')
        try:
            client = BlobClient()
            blob = client.put(
                _blob_path(product_name, uploaded_file.name),
                uploaded_file.read(),
                access='public',
                add_random_suffix=False,
                content_type=getattr(uploaded_file, 'content_type', None),
            )
            return blob['url'], blob['pathname']
        except BlobError as exc:  # pragma: no cover
            raise ProductImageUploadError(f'Image upload failed: {exc}') from exc
        except Exception as exc:  # pragma: no cover
            raise ProductImageUploadError(f'Image upload failed: {exc}') from exc

    # Local fallback when running outside Vercel Blob.
    saved_path = default_storage.save(f"products/{_safe_filename(uploaded_file.name)}", uploaded_file)
    return default_storage.url(saved_path), saved_path


def delete_product_image(product: Product) -> None:
    if product.image_blob_url and delete_blob and os.getenv('BLOB_READ_WRITE_TOKEN'):
        try:
            delete_blob(product.image_blob_url)
        except Exception:
            pass

    if product.image:
        try:
            product.image.delete(save=False)
        except Exception:
            pass

    product.image_blob_url = ''
    product.image_blob_pathname = ''
    product.image = None
