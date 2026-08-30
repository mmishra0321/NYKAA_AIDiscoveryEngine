# Slim query image: cached catalog + FastAPI. No MiniLM / Chroma / torch.
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY config/ config/
COPY src/ src/
COPY data/responses/ data/responses/

EXPOSE 8000

CMD ["python", "-m", "src.api"]
