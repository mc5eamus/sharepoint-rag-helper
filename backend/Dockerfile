# Use an official Python runtime as a parent image
FROM python:3.14-slim AS stage


RUN apt-get update && apt-get install libgl1 libglib2.0-0 -y

# Set the working directory in the container to /app
WORKDIR /app

ADD ./requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# https://stackoverflow.com/questions/76106366/how-to-use-tiktoken-in-offline-mode-computer
RUN python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"

FROM stage AS app

WORKDIR /app

ADD ./*.py /app
ADD ./.env /app

# Make port 80 available to the world outside this container
EXPOSE 80

# Run the command to start uWSGI
CMD ["python", "app.py"]