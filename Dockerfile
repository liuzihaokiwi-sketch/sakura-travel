FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for asyncpg + WeasyPrint (libpango / libcairo / fonts-noto-cjk)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    # WeasyPrint 依赖
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    # CJK 字体（中文不乱码）
    fonts-noto-cjk \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Copy source code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
