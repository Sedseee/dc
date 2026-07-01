# This base image already contains Python AND all the Linux dependencies for Playwright
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Set the working directory inside the container
WORKDIR /app

# Copy all your bot files from GitHub into the container
COPY . /app

# Install your Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD ["python", "bot.py"]
