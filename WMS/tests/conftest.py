"""Pytest configuration and fixtures for WMS tests."""

import pytest
import numpy as np
from PIL import Image
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_image():
    """Create a sample 512x512 RGB image."""
    image_array = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    image = Image.fromarray(image_array, mode="RGB")
    return image


@pytest.fixture
def sample_mask():
    """Create a sample 512x512 binary mask (0 and 255 only)."""
    mask_array = np.random.choice([0, 255], size=(512, 512), p=[0.7, 0.3])
    mask = Image.fromarray(mask_array.astype(np.uint8), mode="L")
    return mask


@pytest.fixture
def sample_image_bytes(sample_image):
    """Create sample image as bytes (for API testing)."""
    import io

    buffer = io.BytesIO()
    sample_image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def training_data_dir(temp_dir, sample_image, sample_mask):
    """Create a temporary training data directory with sample data."""
    images_dir = temp_dir / "images"
    masks_dir = temp_dir / "masks"
    images_dir.mkdir()
    masks_dir.mkdir()

    # Create 3 image/mask pairs
    for i in range(1, 4):
        img_path = images_dir / f"image{i:03d}.jpg"
        mask_path = masks_dir / f"image{i:03d}.png"

        sample_image.save(img_path)
        sample_mask.save(mask_path)

    return temp_dir


@pytest.fixture
def invalid_training_data_dir(temp_dir):
    """Create a training data directory with various issues for testing."""
    images_dir = temp_dir / "images"
    masks_dir = temp_dir / "masks"
    images_dir.mkdir()
    masks_dir.mkdir()

    # Image with wrong resolution
    wrong_size_img = Image.new("RGB", (256, 256), color="red")
    wrong_size_img.save(images_dir / "wrong_size.jpg")

    # Mask with non-binary values
    non_binary_mask = np.random.randint(0, 256, (512, 512), dtype=np.uint8)
    Image.fromarray(non_binary_mask, mode="L").save(masks_dir / "wrong_size.png")

    # Image without corresponding mask
    orphan_img = Image.new("RGB", (512, 512), color="blue")
    orphan_img.save(images_dir / "orphan.jpg")

    # Mask without corresponding image
    orphan_mask = np.zeros((512, 512), dtype=np.uint8)
    Image.fromarray(orphan_mask, mode="L").save(masks_dir / "orphan_mask.png")

    return temp_dir
