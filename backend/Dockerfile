# Use Python 3.10 slim image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies, including TeX Live and Pandoc
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libmagic1 \
    pandoc \
    # Essential TeX Live packages (Lighter version for limited disk space)
    texlive-xetex \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-science \
    texlive-fonts-recommended \
    texlive-bibtex-extra \
    # Font configuration
    fontconfig \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source code and the entry script
COPY backend ./backend
COPY run_api.py .

# Create necessary directories for storage
RUN mkdir -p storage/custom_templates storage/temp_jobs storage/output

# Expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["python", "run_api.py", "--host", "0.0.0.0", "--port", "8000", "--no-reload"]
