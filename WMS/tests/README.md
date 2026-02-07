# Unit Tests

Comprehensive unit tests for the Water Meters Segmentation project.

## Test Coverage

### test_serve_api.py
Tests for the FastAPI serving application:
- **Preprocessing tests**: Image preprocessing, resizing, normalization
- **Postprocessing tests**: Mask generation, binarization, encoding
- **API endpoint tests**: Health check, prediction, metrics
- **Integration tests**: Full prediction workflow

### test_data_qa.py
Tests for data quality assurance:
- **Valid data tests**: Correct image/mask pairs, resolutions, binary masks
- **Invalid data tests**: Missing files, wrong resolutions, non-binary masks
- **Edge cases**: Empty directories, corrupted files, mixed data
- **Statistics tests**: Coverage calculations, resolution detection

## Running Tests

### Install Dependencies

```bash
# Install all requirements including test dependencies
pip install -r requirements.txt
```

Required test packages:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `httpx` - Required for FastAPI TestClient

### Run All Tests

```bash
# From project root
pytest WMS/tests/

# With verbose output
pytest WMS/tests/ -v

# With coverage report
pytest WMS/tests/ --cov=WMS/src --cov-report=html --cov-report=term-missing
```

### Run Specific Tests

```bash
# Run only API tests
pytest WMS/tests/test_serve_api.py

# Run only data QA tests
pytest WMS/tests/test_data_qa.py

# Run specific test function
pytest WMS/tests/test_serve_api.py::test_health_endpoint

# Run tests by marker
pytest -m api  # Only API tests
pytest -m data # Only data tests
```

### Coverage Report

After running tests with coverage, open the HTML report:

```bash
# Generate coverage
pytest --cov=WMS/src --cov-report=html

# Open report (Linux/Mac)
open htmlcov/index.html

# Open report (Windows)
start htmlcov/index.html
```

## Test Configuration

### pytest.ini

Configuration file at project root:
- Test discovery patterns
- Output formatting
- Coverage settings (commented out by default)
- Custom markers

### conftest.py

Shared pytest fixtures:
- `temp_dir` - Temporary directory for file tests
- `sample_image` - 512x512 RGB test image
- `sample_mask` - 512x512 binary mask
- `sample_image_bytes` - Image as bytes for API testing
- `training_data_dir` - Complete training data structure
- `invalid_training_data_dir` - Invalid data for error testing

## CI/CD Integration

Tests run automatically on GitHub Actions for:
- Every push to `main` or `develop` branches
- Every pull request to `main`

See `.github/workflows/ci.yaml` for CI configuration.

## Test Markers

Use markers to categorize and run specific test groups:

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Available Markers

- `unit` - Fast unit tests
- `integration` - Integration tests
- `slow` - Slow-running tests
- `api` - API endpoint tests
- `data` - Data validation tests

## Writing New Tests

### Test Structure

```python
# test_new_feature.py

import pytest
from pathlib import Path

def test_feature_basic():
    """Test basic functionality."""
    assert True

def test_feature_edge_case(temp_dir):
    """Test edge case using fixture."""
    # temp_dir is automatically created and cleaned up
    pass

@pytest.mark.slow
def test_feature_slow():
    """Test that takes a long time."""
    pass
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Use descriptive test names** (`test_function_does_what`)
3. **Use fixtures** for common setup/teardown
4. **Test edge cases** and error conditions
5. **Mock external dependencies** (MLflow, S3, etc.)
6. **Add docstrings** to explain what is being tested

### Example Test

```python
def test_preprocess_image_handles_different_sizes(sample_image):
    """Test preprocessing resizes images to 512x512."""
    # Arrange
    small_image = Image.new("RGB", (256, 256), color="red")

    # Act
    tensor = preprocess_image(small_image)

    # Assert
    assert tensor.shape == (1, 3, 512, 512)
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running from the project root:

```bash
cd /path/to/Water-Meters-Segmentation-Autimatization
pytest WMS/tests/
```

### Missing Dependencies

```bash
# Install missing test dependencies
pip install pytest pytest-cov httpx

# Or reinstall all requirements
pip install -r requirements.txt
```

### Module Not Found: httpx

FastAPI TestClient requires httpx:

```bash
pip install httpx
```

### Coverage Not Working

Install pytest-cov:

```bash
pip install pytest-cov
```

Then uncomment coverage options in `pytest.ini`.

## Test Results Example

```
============================= test session starts ==============================
platform linux -- Python 3.12.0, pytest-8.0.0, pluggy-1.4.0
rootdir: /path/to/project
configfile: pytest.ini
collected 42 items

WMS/tests/test_serve_api.py ...................                          [ 45%]
WMS/tests/test_data_qa.py .......................                        [100%]

============================== 42 passed in 2.34s ==============================
```

## Coverage Goals

Target coverage: **>70%** of source code

Key areas to maintain high coverage:
- API endpoints (>90%)
- Data validation logic (>85%)
- Image preprocessing (>80%)
- Model inference pipeline (>75%)

## Next Steps

- [ ] Add tests for `model.py` (U-Net architecture)
- [ ] Add tests for `dataset.py` (data loading)
- [ ] Add tests for `transforms.py` (data augmentation)
- [ ] Add integration tests for training pipeline
- [ ] Add tests for MLflow integration
- [ ] Increase coverage to >80%

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
