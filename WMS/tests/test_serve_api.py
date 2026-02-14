"""Unit tests for FastAPI serving application."""

import pytest
import sys
from pathlib import Path
import io
import torch
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from WMS.src.serve.app import (
    app,
    preprocess_image,
    postprocess_mask,
    mask_to_base64,
)


@pytest.fixture
def client():
    """Create FastAPI test client."""
    # Override model initialization to use a mock model
    from WMS.src.serve import app as app_module

    # Create a simple mock model
    class MockModel(torch.nn.Module):
        def forward(self, x):
            # Return dummy output with correct shape
            batch_size = x.shape[0]
            return torch.randn(batch_size, 1, 512, 512)

    app_module.model = MockModel()
    app_module.device = torch.device("cpu")
    app_module.model_loaded.set(1)

    return TestClient(app)


# =============================================================================
# Preprocessing Tests
# =============================================================================


def test_preprocess_image(sample_image):
    """Test image preprocessing."""
    tensor = preprocess_image(sample_image)

    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 3, 512, 512)  # Batch, channels, height, width
    assert tensor.dtype == torch.float32


def test_preprocess_image_different_size():
    """Test preprocessing with non-512x512 image (should resize)."""
    image = Image.new("RGB", (256, 256), color="red")
    tensor = preprocess_image(image)

    assert tensor.shape == (1, 3, 512, 512)


# =============================================================================
# Postprocessing Tests
# =============================================================================


def test_postprocess_mask():
    """Test mask postprocessing."""
    # Create dummy model output (logits)
    output = torch.randn(1, 1, 512, 512)

    mask = postprocess_mask(output)

    assert isinstance(mask, np.ndarray)
    assert mask.shape == (512, 512)
    assert mask.dtype == np.uint8
    assert set(np.unique(mask)).issubset({0, 255})  # Binary mask


def test_mask_to_base64():
    """Test mask to base64 encoding."""
    mask = np.random.choice([0, 255], size=(512, 512)).astype(np.uint8)

    base64_str = mask_to_base64(mask)

    assert isinstance(base64_str, str)
    assert len(base64_str) > 0

    # Verify we can decode it back
    import base64

    decoded_bytes = base64.b64decode(base64_str)
    decoded_image = Image.open(io.BytesIO(decoded_bytes))
    assert decoded_image.size == (512, 512)


# =============================================================================
# API Endpoint Tests
# =============================================================================


def test_root_endpoint(client):
    """Test root endpoint returns prediction UI."""
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Water Meters" in response.content


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True


def test_health_endpoint_no_model():
    """Test health check when model is not loaded."""
    from WMS.src.serve import app as app_module

    # Temporarily set model to None
    original_model = app_module.model
    app_module.model = None

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 503

    # Restore model
    app_module.model = original_model


def test_predict_endpoint(client, sample_image_bytes):
    """Test prediction endpoint."""
    files = {"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
    response = client.post("/predict", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "mask_base64" in data
    assert "metadata" in data
    assert data["metadata"]["output_size"] == [512, 512]
    assert "latency_seconds" in data["metadata"]


def test_predict_endpoint_png(client, sample_image):
    """Test prediction with PNG image."""
    buffer = io.BytesIO()
    sample_image.save(buffer, format="PNG")
    buffer.seek(0)

    files = {"image": ("test.png", buffer.getvalue(), "image/png")}
    response = client.post("/predict", files=files)

    assert response.status_code == 200


def test_predict_endpoint_grayscale_conversion(client):
    """Test prediction with grayscale image (should convert to RGB)."""
    # Create grayscale image
    gray_image = Image.new("L", (512, 512), color=128)
    buffer = io.BytesIO()
    gray_image.save(buffer, format="PNG")
    buffer.seek(0)

    files = {"image": ("test.png", buffer.getvalue(), "image/png")}
    response = client.post("/predict", files=files)

    assert response.status_code == 200


def test_predict_endpoint_invalid_file(client):
    """Test prediction with invalid file."""
    files = {"image": ("test.txt", b"not an image", "text/plain")}
    response = client.post("/predict", files=files)

    assert response.status_code == 500


def test_predict_endpoint_no_model():
    """Test prediction when model is not loaded."""
    from WMS.src.serve import app as app_module

    # Temporarily set model to None
    original_model = app_module.model
    app_module.model = None

    client = TestClient(app)
    files = {"image": ("test.jpg", b"fake image data", "image/jpeg")}

    # This will fail because image is invalid, but we're testing the model check
    response = client.post("/predict", files=files)

    assert response.status_code == 503

    # Restore model
    app_module.model = original_model


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    # Check for expected metrics
    content = response.text
    assert "wms_predictions_total" in content
    assert "wms_predict_latency_seconds" in content
    assert "wms_model_loaded" in content


# =============================================================================
# Integration Tests
# =============================================================================


def test_full_prediction_workflow(client, sample_image):
    """Test complete prediction workflow."""
    # 1. Check health
    health_response = client.get("/health")
    assert health_response.status_code == 200

    # 2. Make prediction
    buffer = io.BytesIO()
    sample_image.save(buffer, format="JPEG")
    buffer.seek(0)

    files = {"image": ("test.jpg", buffer.getvalue(), "image/jpeg")}
    predict_response = client.post("/predict", files=files)
    assert predict_response.status_code == 200

    # 3. Verify response structure
    data = predict_response.json()
    assert "mask_base64" in data
    assert len(data["mask_base64"]) > 0

    # 4. Verify we can decode the mask
    import base64

    mask_bytes = base64.b64decode(data["mask_base64"])
    mask_image = Image.open(io.BytesIO(mask_bytes))
    assert mask_image.size == (512, 512)

    # 5. Check metrics were updated
    metrics_response = client.get("/metrics")
    assert "wms_predictions_total" in metrics_response.text
