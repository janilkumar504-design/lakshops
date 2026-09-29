FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir hindsight-client fastapi uvicorn requests pydantic python-dotenv
COPY laksh_ops laksh_ops
COPY static static
COPY server.py .
ENV PORT=8000
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
