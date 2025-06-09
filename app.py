from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, TranscriptsDisabled, CouldNotRetrieveTranscript
import re
import time

# Load environment variables
load_dotenv()

# Get API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    # Log an error if the API key is not set
    print("Error: GROQ_API_KEY environment variable is not set")
    # In a real application, you might return an error to the user or handle this differently
    raise ValueError("GROQ_API_KEY environment variable is not set")

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
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',  # youtu.be/ format
        r'(?:embed\/)([0-9A-Za-z_-]{11})',  # embed/ format
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
    try:
        print(f"Attempting to extract transcript for URL: {youtube_video_url}") # Log URL
        video_id = extract_video_id(youtube_video_url)
        if not video_id:
            print(f"Could not extract video ID from URL: {youtube_video_url}")
            return None, "Invalid YouTube URL. Please check the URL and try again."
        
        print(f"Fetching transcript for video ID: {video_id}")
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                transcript = " ".join([i["text"] for i in transcript_list])
                print("Successfully extracted transcript.") # Log success
                return transcript, None
            except TranscriptsDisabled:
                error_msg = "This video has captions disabled. Please try a different video with captions enabled."
                print(error_msg)
                return None, error_msg
            except NoTranscriptFound:
                error_msg = "No transcript found for this video. Please try a different video with captions enabled."
                print(error_msg)
                return None, error_msg
            except CouldNotRetrieveTranscript as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                error_msg = "Could not retrieve transcript. This might be due to YouTube restrictions. Please try again later."
                print(error_msg)
                return None, error_msg
            except Exception as transcript_error:
                if "no element found" in str(transcript_error).lower():
                    if attempt < max_retries - 1:
                        print(f"XML parsing error, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    error_msg = "Error accessing video transcript. Please try a different video or try again later."
                else:
                    error_msg = f"Error fetching transcript: {str(transcript_error)}"
                print(error_msg)
                return None, error_msg
    except Exception as e:
        error_msg = f"General error in transcript extraction: {str(e)}"
        print(error_msg)
        return None, error_msg

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
    transcript, error = extract_transcript_details(youtube_url)
    if not transcript:
        print(f"Error: {error}") # Log error
        return jsonify({'error': error}), 400
    
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

# Vercel serverless handler
app = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)