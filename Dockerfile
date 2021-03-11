# Set base image (host OS)
FROM python:3.8-buster

# By default, listen on port 5000
EXPOSE 5000/tcp

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .
COPY requirements/prod.txt requirements/prod.txt

# Install any dependencies
RUN pip install -r requirements.txt

# Copy the content of the local src directory to the working directory
# COPY app.py .
# COPY spotify_ranked_playlists.py .
# COPY spotify.py .
# COPY spotify_helpers.py .
# COPY static ./static
# COPY templates ./templates
COPY . .

# Specify the command to run on container start
CMD [ "python", "./app.py" ]
# CMD ["/bin/bash"]
