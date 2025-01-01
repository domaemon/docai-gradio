FROM python:3.12-slim

# Create app directory
WORKDIR /app

# Bundle app source
COPY . /app

# Install app dependencies
RUN pip install -r requirements.txt

ARG PROJECT_ID 
ARG GCP_DOCAI_REGION
ARG GCP_DOCAI_PROCESSOR_ID

ENV GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=8080 \
    PROJECT_ID="${PROJECT_ID}" \
    GCP_DOCAI_REGION="${GCP_DOCAI_REGION}" \
    GCP_DOCAI_PROCESSOR_ID="${GCP_DOCAI_PROCESSOR_ID}"

EXPOSE 8080

CMD [ "python", "app.py"]
