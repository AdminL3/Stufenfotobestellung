# 1. Use Python 3.11-slim for better compatibility with NumPy/PyArrow
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install system tools required to compile certain Python packages
# This fixes the "cmake not found" and "g++" errors
RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements and install them
# We do this before copying the code to take advantage of Docker's layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code into /app
COPY . .

# 6. Ensure the 'helper' directory is treated as a package
# This creates an empty __init__.py if it doesn't already exist
RUN touch helper/__init__.py

# 7. Expose the default Streamlit port
EXPOSE 8501

# 8. Start the app from the root directory (/app)
# This ensures that "import helper" works correctly
CMD ["streamlit", "run", "form.py", "--server.port=8501", "--server.address=0.0.0.0"]