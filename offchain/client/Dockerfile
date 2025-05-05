FROM python:3.10-slim
WORKDIR /app

COPY client/   /app/client/
COPY common/   /app/common/
COPY Moderator.json /app/Moderator.json

RUN pip install --no-cache-dir websockets fastapi uvicorn python-dotenv eth-account web3 docker
CMD ["python", "/app/client/exchange.py", "-l"]
