FROM python:3.10-slim

# Install TeX Live and system dependencies
RUN apt-get update && apt-get install -y texlive-xetex texlive-fonts-recommended texlive-fonts-extra texlive-latex-extra fontconfig && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend source code
COPY . .

# Expose port 8000
EXPOSE 8000

# Command to run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
