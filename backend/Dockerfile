# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster as stage


RUN apt-get update && apt-get install libgl1 libglib2.0-0 -y

# Set the working directory in the container to /app
WORKDIR /app

ADD ./requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ADD ./whl/azure_search_documents-11.4.0b12-py3-none-any.whl /app

RUN pip install azure_search_documents-11.4.0b12-py3-none-any.whl
RUN rm azure_search_documents-11.4.0b12-py3-none-any.whl

# https://stackoverflow.com/questions/76106366/how-to-use-tiktoken-in-offline-mode-computer
RUN python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"

FROM stage as app

WORKDIR /app

ADD ./*.py /app

# Make port 8085 available to the world outside this container
EXPOSE 8085

# Run the command to start uvicorn
CMD ["python", "app.py"]