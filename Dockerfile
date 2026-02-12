# Use official Python image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Expose port (only if using Streamlit)
EXPOSE 8501

# Command to run the app
CMD ["streamlit", "run", "app.py"]
