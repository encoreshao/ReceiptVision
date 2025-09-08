# ReceiptVision 📄✨

**Advanced OCR Application for Bank Invoices and Consumer Receipts**

ReceiptVision is a comprehensive Python-based OCR application that transforms receipts and invoices into structured data using advanced image processing and machine learning techniques. Built with a modern Apple-inspired UI and robust backend architecture.

![ReceiptVision Demo](https://via.placeholder.com/800x400/007AFF/FFFFFF?text=ReceiptVision+Demo)

## 🌟 Key Features

### 📁 Multi-Format Support
- **PDF Documents**: Extract text and convert pages to images
- **Image Formats**: PNG, JPG, JPEG, BMP, TIFF support
- **Automatic Detection**: Smart file type recognition and processing

### 🧠 Advanced OCR Processing
- **Smart Data Extraction**: Merchant names, dates, amounts, and itemized purchases
- **Confidence Scoring**: Field-level and overall processing confidence metrics
- **Multi-Language Support**: Configurable OCR language models

### 🖼️ Advanced Image Processing
- **Denoising**: Multiple denoising algorithms for cleaner text extraction
- **Adaptive Thresholding**: Gaussian and mean adaptive thresholding
- **Morphological Operations**: Text cleanup and enhancement
- **Skew Correction**: Automatic image rotation and alignment
- **Contrast Enhancement**: CLAHE and custom enhancement algorithms

### ⚡ Batch Processing
- **Multiple File Upload**: Process dozens of files simultaneously
- **Progress Tracking**: Real-time processing status and progress bars
- **Job Management**: Named batch jobs with detailed statistics
- **Error Handling**: Individual file error tracking and reporting

### 🎨 Modern Web Interface
- **Apple-Inspired Design**: Clean, modern UI following Apple's design principles
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Real-Time Updates**: Live progress tracking and notifications
- **Intuitive Navigation**: Easy-to-use interface for all skill levels

### 🗄️ Data Management
- **PostgreSQL Storage**: Robust database with full ACID compliance
- **Search & Filter**: Advanced search capabilities across all receipts
- **Data Export**: Multiple export formats for extracted data
- **Audit Trail**: Complete processing history and metadata

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Tesseract OCR engine
- Git

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/encoreshao/ReceiptVision.git
   cd ReceiptVision
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install System Dependencies**

   **macOS (using Homebrew):**
   ```bash
   brew install tesseract
   brew install poppler  # For PDF processing
   ```

   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install tesseract-ocr
   sudo apt-get install poppler-utils
   sudo apt-get install libpq-dev  # For PostgreSQL
   ```

   **Windows:**
   - Download and install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
   - Download and install [Poppler](https://blog.alivate.com.au/poppler-windows/)
   - Add both to your system PATH

5. **Set Up PostgreSQL Database**
   ```bash
   # Create database
   createdb receiptvision

   # Create user (optional)
   psql -c "CREATE USER receiptvision_user WITH PASSWORD 'your_password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE receiptvision TO receiptvision_user;"
   ```

6. **Configure Environment Variables**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials and settings
   ```

7. **Initialize Database**
   ```bash
   python migrations/init_db.py
   ```

8. **Run the Application**
   ```bash
   python app.py
   ```

9. **Access the Application**
   Open your browser and navigate to `http://localhost:5001`

## 📖 Usage Guide

### Single File Processing

1. **Navigate to Upload Page**: Click "Upload" in the navigation menu
2. **Select File**: Drag and drop or click to browse for your receipt/invoice
3. **Process**: Click "Process File" to start OCR processing
4. **Review Results**: View extracted data with confidence scores
5. **View Details**: Click "View Full Details" for complete information

### Batch Processing

1. **Navigate to Batch Page**: Click "Batch" in the navigation menu
2. **Add Files**: Drag and drop multiple files or browse to select
3. **Name Your Job**: Optionally provide a descriptive name for the batch
4. **Start Processing**: Click "Start Batch Processing"
5. **Monitor Progress**: Watch real-time progress updates
6. **Review Results**: View completion statistics and individual file results

### Managing Receipts

1. **View All Receipts**: Navigate to the "Receipts" page
2. **Search & Filter**: Use the search bar and filters to find specific receipts
3. **View Details**: Click on any receipt to see full extracted data
4. **Export Data**: Use export options to download data in various formats

## 🏗️ Architecture

### Backend Components

```
ReceiptVision/
├── app.py                     # Flask application factory
├── models.py                  # SQLAlchemy database models
├── api/
│   ├── routes.py             # Main API blueprint registration
│   └── blueprints/           # Resource-specific route blueprints
│       ├── __init__.py       # Blueprint package initialization
│       ├── upload_routes.py  # File upload endpoints
│       ├── receipt_routes.py # Receipt management endpoints
│       ├── batch_routes.py   # Batch processing endpoints
│       ├── system_routes.py  # Health/statistics endpoints
│       └── utils.py          # Shared API utilities
├── web/
│   └── routes.py             # Web interface routes
├── services/
│   ├── file_processor.py     # File processing service
│   └── batch_processor.py    # Batch processing service
├── ocr/
│   ├── ocr_engine.py         # Main OCR processing engine
│   ├── image_processor.py    # Advanced image preprocessing
│   └── pdf_processor.py      # PDF handling and conversion
├── tests/
│   ├── conftest.py           # Pytest configuration
│   ├── test_api.py           # API endpoint tests
│   ├── test_models.py        # Database model tests
│   ├── test_ocr.py           # OCR processing tests
│   └── test_services.py      # Service layer tests
└── migrations/
    └── init_db.py            # Database initialization
```

### Frontend Components

```
static/
├── css/
│   └── style.css         # Apple-inspired CSS styles
├── js/
│   └── main.js          # Core JavaScript functionality
templates/
├── base.html            # Base template with navigation
├── index.html           # Homepage with features showcase
├── upload.html          # Single file upload interface
├── batch.html           # Batch processing interface
├── receipts.html        # Receipt management interface
├── receipt_detail.html  # Individual receipt details
└── statistics.html      # Application statistics
```

### Database Schema

- **receipts**: File metadata and processing status
- **extracted_data**: OCR results and structured data
- **batch_jobs**: Batch processing job tracking

### API Blueprint Architecture

The API is organized using Flask blueprints for better maintainability:

- **📤 Upload Routes** (`upload_routes.py`): File upload and processing endpoints
- **📄 Receipt Routes** (`receipt_routes.py`): Receipt management and retrieval
- **📦 Batch Routes** (`batch_routes.py`): Batch job management and status
- **⚙️ System Routes** (`system_routes.py`): Health checks and statistics
- **🔧 Utils** (`utils.py`): Shared utilities and helper functions

Each blueprint is registered under the `/api/v1` prefix and handles specific resource domains, making the codebase more modular and easier to maintain.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `UPLOAD_FOLDER` | File upload directory | `uploads` |
| `MAX_CONTENT_LENGTH` | Maximum file size (bytes) | `16777216` (16MB) |
| `TESSERACT_CMD` | Tesseract executable path | `/usr/local/bin/tesseract` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

### OCR Configuration

The OCR engine can be configured for different languages and processing modes:

```python
# In ocr/ocr_engine.py
custom_config = r'--oem 3 --psm 6 -l eng+fra+deu'  # Multiple languages
```

### Image Processing Parameters

Fine-tune image processing in `ocr/image_processor.py`:

```python
# Contrast enhancement
alpha = 1.2  # Contrast control (1.0-3.0)
beta = 10    # Brightness control (0-100)

# Denoising parameters
cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_api.py -v
pytest tests/test_models.py -v
pytest tests/test_ocr.py -v

# Run with coverage report
pytest --cov=. --cov-report=html --cov-report=term

# Run tests in parallel (faster)
pytest -n auto
```

### Test Organization

- **`test_api.py`**: API endpoint testing
- **`test_models.py`**: Database model testing
- **`test_ocr.py`**: OCR processing testing
- **`test_services.py`**: Service layer testing
- **`conftest.py`**: Shared pytest fixtures and configuration

## 📊 Performance Optimization

### Database Optimization
- Indexes on frequently queried columns
- Connection pooling for high-traffic scenarios
- Query optimization for large datasets

### Image Processing Optimization
- Multi-threading for batch processing
- Image caching for repeated processing
- Memory-efficient processing for large files

### API Performance
- Response caching for static data
- Pagination for large result sets
- Asynchronous processing for long-running tasks

## 🔒 Security Considerations

### File Upload Security
- File type validation and sanitization
- Size limits to prevent DoS attacks
- Temporary file cleanup after processing

### Database Security
- Parameterized queries to prevent SQL injection
- User input validation and sanitization
- Database connection encryption

### API Security
- Rate limiting for API endpoints
- CORS configuration for cross-origin requests
- Input validation for all endpoints

## 🚀 Deployment

### Production Deployment with Docker

The project includes production-ready Docker configuration:

1. **Using Docker Compose**
   ```bash
   # Start all services
   docker-compose up -d

   # View logs
   docker-compose logs -f

   # Stop services
   docker-compose down
   ```

2. **Services Configuration**
   - **Web Application**: Flask app with Gunicorn server on port 5000
   - **Database**: PostgreSQL 13 with persistent data storage
   - **Reverse Proxy**: Nginx for static files and SSL termination
   - **Health Checks**: Built-in health monitoring for all services

3. **Environment Variables**
   Update the docker-compose.yml with your production settings:
   ```yaml
   environment:
     - DATABASE_URL=postgresql://your_user:your_pass@db:5432/receiptvision
     - SECRET_KEY=your-production-secret-key
     - FLASK_ENV=production
   ```

### Cloud Deployment Options

- **AWS**: EC2 + RDS + S3 for file storage
- **Google Cloud**: App Engine + Cloud SQL + Cloud Storage
- **Azure**: App Service + Azure Database + Blob Storage
- **Heroku**: Web dyno + Heroku Postgres + Cloudinary

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Submit a pull request

### Code Style & Development Guidelines

The project includes comprehensive development guidelines in `.cursor/rules` for:

- **Architecture Patterns**: Flask application factory, blueprint organization, service layer
- **Code Standards**: PEP 8 compliance, type hints, Google-style docstrings
- **API Development**: RESTful conventions, error handling, response formats
- **Database Patterns**: SQLAlchemy best practices, relationship management
- **Testing Guidelines**: pytest patterns, fixture usage, coverage requirements
- **Security Considerations**: Input validation, file upload security, SQL injection prevention

### Key Conventions

- Follow PEP 8 for Python code
- Use type hints for all function parameters and return values
- Add Google-style docstrings to all functions and classes
- Organize routes by resource using blueprints
- Implement business logic in service layer, not route handlers
- Write comprehensive tests for new features
- Use meaningful variable and function names
- Implement proper error handling and logging

## 📝 API Documentation

### Core Endpoints

#### Upload & Processing
```http
# Upload single file
POST /api/v1/upload
Content-Type: multipart/form-data
file: [binary file data]

# Batch upload multiple files
POST /api/v1/batch-upload
Content-Type: multipart/form-data
files: [multiple binary files]
job_name: "Optional job name"
```

#### Receipt Management
```http
# Get specific receipt
GET /api/v1/receipt/{receipt_id}

# List all receipts with pagination
GET /api/v1/receipts?page=1&per_page=10&status=completed

# Get detailed receipt information
GET /api/v1/receipts/{receipt_id}

# Download original receipt file
GET /api/v1/receipts/{receipt_id}/file
```

#### Batch Job Management
```http
# Get batch job status
GET /api/v1/batch-job/{job_id}

# List all batch jobs
GET /api/v1/batch-jobs?page=1&per_page=10
```

#### System Information
```http
# Health check
GET /api/v1/health

# Application statistics
GET /api/v1/statistics
```

### Response Format
All API responses follow a consistent JSON structure:

```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully"
}
```

Error responses:
```json
{
  "error": "Description of the error",
  "code": "ERROR_CODE"
}
```

## 🐛 Troubleshooting

### Common Issues

**Tesseract not found:**
```bash
# macOS
brew install tesseract
export TESSERACT_CMD=/usr/local/bin/tesseract

# Ubuntu
sudo apt-get install tesseract-ocr
```

**PDF processing fails:**
```bash
# Install poppler-utils
sudo apt-get install poppler-utils  # Ubuntu
brew install poppler  # macOS
```

**Database connection errors:**
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists and user has permissions

**Low OCR accuracy:**
- Ensure images are high resolution (300+ DPI)
- Check image quality and contrast
- Try different OCR language models
- Adjust image preprocessing parameters

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for optical character recognition
- [OpenCV](https://opencv.org/) for image processing capabilities
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [PostgreSQL](https://www.postgresql.org/) for robust data storage
- [Apple Design Guidelines](https://developer.apple.com/design/) for UI inspiration

## 📞 Support

- **Documentation**: [Wiki](https://github.com/encoreshao/ReceiptVision/wiki)
- **Issues**: [GitHub Issues](https://github.com/encoreshao/ReceiptVision/issues)
- **Discussions**: [GitHub Discussions](https://github.com/encoreshao/ReceiptVision/discussions)
- **Email**: support@receiptvision.com

---

**Built with ❤️ for accurate receipt processing**
