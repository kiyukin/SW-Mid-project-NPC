FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ backend/
ENV NPC_HOST=0.0.0.0
ENV NPC_PORT=8089
ENV PYTHONUNBUFFERED=1
EXPOSE 8089
CMD ["python", "-m", "backend.main"]
