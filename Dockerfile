FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python3 -m spacy download en_core_web_sm

COPY app/ .

ENV JWT_SECRET_KEY="s3cr3t_k3y_1234567890"
ENV KUBECONFIG=/root/.kube/config
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["python3", "server.py"]