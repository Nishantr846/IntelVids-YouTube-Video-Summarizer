from flask import Flask, render_template, request, jsonify
import streamlit as st
from dotenv import load_dotenv
import os
import requests
from youtube_transcript_api import YouTubeTranscriptApi
import re
import random
import time
from proxy_config import PROXY_LIST, PROXY_ROTATION_ENABLED, MAX_RETRIES, RETRY_DELAY

# Load environment variables
load_dotenv()

# Get API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    # Log an error if the API key is not set
    print("Error: GROQ_API_KEY environment variable is not set")
    # In a real application, you might return an error to the user or handle this differently
    raise ValueError("GROQ_API_KEY environment variable is not set")

def get_random_proxy():
    """Get a random proxy from the proxy list"""
    if not PROXY_LIST or not PROXY_ROTATION_ENABLED:
        return None
    return random.choice(PROXY_LIST)

# Prompt template
prompt_template = """You are a YouTube video summarizer. Summarize the following transcript into clear bullet points, within 250 words:\n\n"""

def extract_video_id(url):
    """
    Extracts the YouTube video ID from various possible YouTube URL formats.
    """
    print(f"Attempting to extract video ID from URL: {url}") # Log URL
    # Patterns for different YouTube URL formats
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',  # v= or / followed by 11-char ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            print(f"Successfully extracted video ID: {video_id}") # Log extracted ID
            return video_id
    print("Could not extract video ID.") # Log failure
    return None

# Extract transcript from YouTube
def extract_transcript_details(youtube_video_url):
    video_id = extract_video_id(youtube_video_url)
    if not video_id:
        print(f"Could not extract video ID from URL: {youtube_video_url}")
        return None

    for attempt in range(MAX_RETRIES):
        try:
            print(f"Attempt {attempt + 1} of {MAX_RETRIES} to extract transcript")
            
            # Configure proxy settings
            proxy = get_random_proxy()
            if proxy:
                os.environ['HTTPS_PROXY'] = proxy
                os.environ['HTTP_PROXY'] = proxy
                print(f"Using proxy: {proxy}")

            # Try to get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = " ".join([i["text"] for i in transcript_list])
            print("Successfully extracted transcript.")
            return transcript

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            
            # Clean up proxy settings
            if proxy:
                del os.environ['HTTPS_PROXY']
                del os.environ['HTTP_PROXY']
            
            # If this was the last attempt, try one final time without proxy
            if attempt == MAX_RETRIES - 1:
                try:
                    print("Final attempt without proxy...")
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                    transcript = " ".join([i["text"] for i in transcript_list])
                    print("Successfully extracted transcript without proxy.")
                    return transcript
                except Exception as e2:
                    print(f"Final attempt failed: {e2}")
                    return None
            
            # Wait before next attempt
            time.sleep(RETRY_DELAY)
    
    return None

# Generate content using LLaMA 3 on Groq API
def generate_llama_summary(transcript_text, prompt):
    print("Attempting to generate summary with LLM.") # Log attempt
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful summarizer."},
            {"role": "user", "content": prompt + transcript_text}
        ],
        "temperature": 0.5,
        "max_tokens": 1024
    }
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        print("Successfully generated summary from LLM.") # Log success
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error generating summary: {e}") # Log error
        return f"Error generating summary: {e}"

def markdown_to_html(text):
    print("Converting markdown to HTML.") # Log attempt
    # Convert **bold** to <b> and *italic* to <i>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Convert lines starting with * or - to <li>
    lines = text.split('\n')
    html_lines = []
    in_list = False
    for line in lines:
        if re.match(r'^\s*([*-])\s+', line):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append('<li>' + re.sub(r'^\s*([*-])\s+', '', line) + '</li>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if line.strip():
                html_lines.append('<p>' + line.strip() + '</p>')
    if in_list:
        html_lines.append('</ul>')
    print("Markdown conversion complete.") # Log success
    return '\n'.join(html_lines)

app = Flask(__name__)

# Home route: serves the main page
@app.route('/')
def index():
    print("Root route '/' accessed.") # Log access
    return render_template('index.html')

# Summarize route: receives YouTube URL and returns summary
@app.route('/summarize', methods=['POST'])
def summarize():
    print("Summarize route '/summarize' accessed.") # Log access
    data = request.get_json()
    youtube_url = data.get('url')
    
    if not youtube_url:
        print("Error: No URL provided in summarize request.") # Log error
        return jsonify({'error': 'No URL provided'}), 400
    
    # Extract video ID and generate thumbnail URL
    video_id = extract_video_id(youtube_url)
    thumbnail_url = None
    if video_id:
        thumbnail_url = f"http://img.youtube.com/vi/{video_id}/0.jpg" # Standard thumbnail URL

    # Extract transcript
    transcript = extract_transcript_details(youtube_url)
    if not transcript:
        print("Error: Could not extract transcript.") # Log error
        return jsonify({'error': 'Could not extract transcript. Make sure the video has captions enabled.'}), 400
    
    # Generate summary using LLM
    summary = generate_llama_summary(transcript, prompt_template)
    if summary.startswith('Error'):
        print(f"Error generating summary: {summary}") # Log error from LLM function
        return jsonify({'error': summary}), 500
    
    # Convert summary to HTML for better formatting
    summary_html = markdown_to_html(summary)

    # Return summary HTML and thumbnail URL
    print("Returning summary and thumbnail.") # Log success
    return jsonify({'summary': summary_html, 'thumbnail_url': thumbnail_url}) # Include thumbnail_url

if __name__ == '__main__':
    app.run(debug=True)