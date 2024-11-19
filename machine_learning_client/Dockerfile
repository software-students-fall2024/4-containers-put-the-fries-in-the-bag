FROM python:3.10-slim

# Install CMake, build-essential, and other dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    liblapack-dev \
    libblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy Pipfile and Pipfile.lock and install dependencies with pipenv
COPY Pipfile Pipfile.lock ./
RUN python -m pip install --upgrade pip
RUN pip install pipenv && pipenv install --deploy --ignore-pipfile

# Copy the application code
COPY . .

# Copy the images folder
COPY images /app/images

# Expose the port the Flask app runs on
EXPOSE 5000

# Command to run the Flask application
CMD ["pipenv", "run", "flask", "run", "--host=0.0.0.0", "--port=5000"]