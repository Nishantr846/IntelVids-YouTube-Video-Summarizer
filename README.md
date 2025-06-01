# IntelVids - Extract intelligence from YouTube video content

A Flask-based web application that summarizes YouTube videos using AI.

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/Nishantr846/IntelVids-YouTube-Video-Summarizer.git
cd IntelVids-YouTube-Video-Summarizer
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory and add your API keys and proxy configuration:
```bash
# Groq API Key
GROQ_API_KEY=your-groq-api-key-here

# Proxy Configuration (required for YouTube transcript extraction)
PROXY_USERNAME=your-proxy-username
PROXY_PASSWORD=your-proxy-password
PROXY_HOST=your-proxy-host
PROXY_PORT=your-proxy-port
```

5. Run the application:
```bash
python app.py
```

## Environment Variables

Create a `.env` file with the following variables:
- `GROQ_API_KEY`: Your Groq API key
- `PROXY_USERNAME`: Your proxy service username
- `PROXY_PASSWORD`: Your proxy service password
- `PROXY_HOST`: Your proxy service host
- `PROXY_PORT`: Your proxy service port

## Proxy Setup

To handle YouTube's IP restrictions, this application uses a proxy service. You'll need to:

1. Sign up for a proxy service (recommended services):
   - Bright Data (formerly Luminati)
   - Oxylabs
   - SmartProxy
   - IPRoyal
   - ProxyMesh

2. Get your proxy credentials from the service

3. Add the credentials to your `.env` file

## Security Note

Never commit your `.env` file or expose your API keys. The `.env` file is already in `.gitignore` to prevent accidental commits.

## Deployment

When deploying to Azure:

1. Add your environment variables in the Azure Portal:
   - Go to your App Service
   - Navigate to Configuration
   - Add all the environment variables from your `.env` file

2. Make sure to set up your proxy credentials in the Azure environment variables as well. 