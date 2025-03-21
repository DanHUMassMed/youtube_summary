import argparse
from youtube_transcript_api import YouTubeTranscriptApi
import re
import requests
from urllib.parse import urlencode
from PIL import Image
from io import BytesIO


def extract_video_id(youtube_url):
    """
    Extract the YouTube video ID from a URL.
    Handles various YouTube URL formats.
    """
    video_id_match = re.search(r'(?:v=|\/videos\/|youtu.be\/|\/v\/|\/e\/|\/watch\?v=|&v=|\/embed\/|%2Fvideos%2F|embed%2F|youtu.be%2F|%2Fv%2F|%2Fe%2F|youtube.com\/embed\/|youtube.com\/v\/|youtube.com\/watch\?v=)([^#\&\?\n\/]+)', youtube_url)
    
    if video_id_match:
        return video_id_match.group(1)
    else:
        raise ValueError("Could not extract video ID from URL. Please provide a valid YouTube URL.")


def get_transcript(video_id, output_file=None, language='en'):

    try:
        # Get the transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        
        # Combine all transcript pieces into one text
        transcript_text = ""
        for entry in transcript_list:
            transcript_text += entry['text'] + " "
        
        # Clean up the text
        transcript_text = transcript_text.strip()
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            
        return transcript_text
    
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_video_title(video_id, api_key):
    if not video_id or not api_key:
        raise ValueError("Invalid video_id or api_key")

    # Construct the API request URL
    base_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": api_key
    }
    url = f"{base_url}?{urlencode(params)}"
    
    try:
        # Send the API request
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        
        title=""
        
        # Validate response and extract the video title
        if "items" in data and len(data["items"]) > 0:
            title = data["items"][0]["snippet"]["title"]
                
        return title
            
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"Network or API error: {e}")
    except ValueError as e:
        raise ValueError(f"Error parsing response: {e}")
    except KeyError:
        raise KeyError("Expected data not found in the response")

def get_video_thumbnail(video_id, api_key, save_path):
    
    if not video_id or not api_key or not save_path:
        print("Invalid parameters provided.")
        return False
    
    # Construct YouTube API request URL
    base_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": api_key
    }
    url = f"{base_url}?{urlencode(params)}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching video details: {e}")
        return None
    except ValueError:
        print("Error parsing JSON response.")
        return None

    # Check if the video data exists and extract thumbnail URL
    if "items" in data and len(data["items"]) > 0:
        thumbnail_url = data["items"][0]["snippet"]['thumbnails']['medium']['url']
        download_image(thumbnail_url, save_path)
        return thumbnail_url
    else:
        print("Video not found or no thumbnail available.")
        return None

def download_image(url, save_path):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        img = Image.open(BytesIO(response.content))
        img.verify()
        
        # If the image is valid, save it
        img = Image.open(BytesIO(response.content))  # Reopen the image after verification
        img.save(save_path)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return False
    except (IOError, SyntaxError) as e:
        print(f"Error verifying or saving the image: {e}")
        return False
    
def chunk_text(file_path, chunk_size, overlap_size):
    """
    Reads a text file and splits it into chunks of the specified size with overlapping content.
    
    Args:
        file_path (str): The path to the text file to be read.
        chunk_size (int): The size of each chunk in characters.
        overlap_size (int): The number of characters to overlap between consecutive chunks.
        
    Returns:
        list: A list of strings, each representing a chunk of the file's content.
    """
    if overlap_size >= chunk_size:
        raise ValueError("Overlap size must be less than chunk size.")

    chunks = []
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
        start = 0
        while start < len(file_content):
            end = start + chunk_size
            chunk = file_content[start:end]
            chunks.append(chunk)
            start = end - overlap_size  # Move the start position back by overlap_size
    return chunks

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YouTube video transcript")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("-o", "--output", help="Output file name", default=None)
    parser.add_argument("-l", "--language", help="Language code (default: en)", default="en")
    
    args = parser.parse_args()
    url="https://youtu.be/ZPUtA3W-7_I?si=M3RCw7uKRLmD3qhZ"
    output="lex.txt"
    language="en"
    get_transcript(url, output, language)