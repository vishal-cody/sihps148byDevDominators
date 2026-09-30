FROM python:3.11-slim

WORKDIR /app

# System deps for WeasyPrint, psycopg2, etc.
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev libffi-dev libcairo2 libpango-1.0-0 \
    libpangocairo-1.0-0 libgdk-pixbuf2.0-0 shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy compiler package
COPY compiler /compiler
RUN pip install -e /compiler 2>/dev/null || true

COPY backend/ .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
