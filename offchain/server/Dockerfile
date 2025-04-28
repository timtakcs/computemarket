FROM python:3.10-slim
WORKDIR /app

COPY server/   /app/server/
COPY common/   /app/common/

RUN pip install --no-cache-dir websockets fastapi uvicorn python-dotenv
WORKDIR /app/server
EXPOSE 8000
EXPOSE 8765
CMD ["python", "wsserver.py"]
