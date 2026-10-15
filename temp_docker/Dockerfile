FROM python:3.12-slim

# Runtime-only container for the cloud gateway component.
# The Windows Tkinter/WinINet GUI and mobile PWA remain outside this container.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8888

WORKDIR /app

# Install only the Python packages required by the project specification.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project source into the image.
COPY . .

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8888

# The project specification names cloud_server.py as the gateway entry point.
CMD ["python", "cloud_server.py"]
