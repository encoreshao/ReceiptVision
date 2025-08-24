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
   Open your browser and navigate to `http://localhost:5000`

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
├── app.py                 # Flask application factory
├── models.py              # SQLAlchemy database models
├── api/
│   └── routes.py         # REST API endpoints
├── web/
│   └── routes.py         # Web interface routes
├── services/
│   ├── file_processor.py # File processing service
│   └── batch_processor.py# Batch processing service
├── ocr/
│   ├── ocr_engine.py     # Main OCR processing engine
│   ├── image_processor.py# Advanced image preprocessing
│   └── pdf_processor.py  # PDF handling and conversion
└── migrations/
    └── init_db.py        # Database initialization
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
└── receipts.html        # Receipt management interface
```

### Database Schema

- **receipts**: File metadata and processing status
- **extracted_data**: OCR results and structured data
- **batch_jobs**: Batch processing job tracking

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

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run Integration Tests
```bash
pytest tests/integration/ -v
```

### Test Coverage
```bash
pytest --cov=. --cov-report=html
```

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

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       tesseract-ocr \
       poppler-utils \
       libpq-dev \
       && rm -rf /var/lib/apt/lists/*

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY . .

   EXPOSE 5000
   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
   ```

2. **Docker Compose Setup**
   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       ports:
         - "5000:5000"
       environment:
         - DATABASE_URL=postgresql://user:pass@db:5432/receiptvision
       depends_on:
         - db

     db:
       image: postgres:13
       environment:
         - POSTGRES_DB=receiptvision
         - POSTGRES_USER=user
         - POSTGRES_PASSWORD=pass
       volumes:
         - postgres_data:/var/lib/postgresql/data

   volumes:
     postgres_data:
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

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Write unit tests for new features

## 📝 API Documentation

### Upload Single File
```http
POST /api/v1/upload
Content-Type: multipart/form-data

file: [binary file data]
```

### Batch Upload
```http
POST /api/v1/batch-upload
Content-Type: multipart/form-data

files: [multiple binary files]
job_name: "Optional job name"
```

### Get Receipt Data
```http
GET /api/v1/receipt/{receipt_id}
```

### List Receipts
```http
GET /api/v1/receipts?page=1&per_page=10&status=completed
```

For complete API documentation, visit `/api/docs` when running the application.

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
