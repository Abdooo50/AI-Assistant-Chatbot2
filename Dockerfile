# Use the official Python 3.12 image from Docker Hub
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    && curl -sSL https://packages.microsoft.com/keys/microsoft.asc -o microsoft.asc \
    && gpg --dearmor < microsoft.asc > /usr/share/keyrings/microsoft-prod.gpg \
    && rm microsoft.asc \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory in the container
WORKDIR /app

# Copy project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 8080

# Start FastAPI using Uvicorn
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8080"]
