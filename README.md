# SD-Host: Stable Diffusion RESTful API Service

A cross-platform Python web service that provides RESTful APIs for Stable Diffusion image generation, supporting Windows, Linux, and macOS.

## Features

- 🌐 RESTful API interface for Stable Diffusion
- 🖥️ Cross-platform support (Windows/Linux/macOS)
- 🚀 High-performance image generation
- 📊 Request tracking and history
- 🔧 Easy configuration and deployment

## Project Structure

```
sd-host/
├── src/                    # Source code
│   ├── api/               # API endpoints
│   ├── core/              # Core Stable Diffusion logic
│   ├── models/            # Data models
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── tests/                 # Test files
├── scripts/               # Deployment and utility scripts
├── requirements/          # Requirements files
├── models/                # Model files (gitignored)
├── output/                # Generated images (gitignored)
├── data/                  # SQLite database files (gitignored)
└── docs/                  # Documentation
```

## Quick Start

### Prerequisites

- Python 3.8 or higher
- CUDA-compatible GPU (recommended)
- 8GB+ RAM
- 10GB+ free disk space

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sd-host
```

2. Create a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements/requirements.txt
```

4. Set up configuration:
```bash
cp config/config.example.yml config/config.yml
# Edit config/config.yml according to your needs
```

5. Run the service:
```bash
python src/main.py
```

## API Documentation

### Generate Image

**POST** `/api/v1/generate`

Generate an image using Stable Diffusion.

#### Request Body
```json
{
  "prompt": "A beautiful landscape with mountains and lake",
  "negative_prompt": "blurry, low quality",
  "width": 512,
  "height": 512,
  "steps": 20,
  "cfg_scale": 7.5,
  "seed": -1
}
```

#### Response
```json
{
  "success": true,
  "task_id": "uuid-string",
  "image_url": "/api/v1/images/uuid-string.png",
  "metadata": {
    "width": 512,
    "height": 512,
    "steps": 20,
    "cfg_scale": 7.5,
    "seed": 12345,
    "execution_time": 15.23
  }
}
```

### Get Image

**GET** `/api/v1/images/{image_id}`

Retrieve a generated image.

### Get Task Status

**GET** `/api/v1/tasks/{task_id}`

Check the status of a generation task.

## Configuration

Configuration is managed through YAML files in the `config/` directory:

- `config.yml`: Main configuration file
- `config.example.yml`: Example configuration template

### Key Configuration Options

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

stable_diffusion:
  model_path: "./models/stable-diffusion-v1-5"
  device: "cuda"  # or "cpu"
  precision: "fp16"  # or "fp32"

storage:
  output_dir: "./output"
  database_path: "./data/sd_host.db"
  max_images: 1000
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src
```

### Code Style

This project uses:
- `black` for code formatting
- `flake8` for linting
- `isort` for import sorting

```bash
# Format code
black src/ tests/

# Check linting
flake8 src/ tests/

# Sort imports
isort src/ tests/
```

## Deployment

### Docker

```bash
# Build image
docker build -t sd-host .

# Run container
docker run -p 8000:8000 sd-host
```

### Systemd Service (Linux)

See `scripts/systemd/sd-host.service` for systemd service configuration.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Stable Diffusion by Stability AI
- Diffusers library by Hugging Face
- FastAPI for the web framework

## Support

For support and questions, please open an issue on the GitHub repository.
