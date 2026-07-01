# Update to match the exact Playwright version (1.61.0)
FROM mcr.microsoft.com/playwright/python:v1.61.0-jammy

# Set the working directory inside the container
WORKDIR /app

# Copy all your bot files from GitHub into the container
COPY . /app

# Install your Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD ["python", "bot.py"]
