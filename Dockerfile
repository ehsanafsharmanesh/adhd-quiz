# Use the official Python image
FROM python:3.11-slim

# Set the working directory to /code
WORKDIR /code

# Copy the requirements file and install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy all the project files into the Docker container
COPY . .

# Expose port 7860 (Hugging Face Spaces requires apps to run on port 7860)
EXPOSE 7860

# Run the Flask app on port 7860 using gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--workers", "1", "--timeout", "120"]
