import os
from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import re
from urllib.parse import urlparse, parse_qs
import json
import traceback
import sqlite3
from datetime import datetime
import uuid
import time

# Load environment variables
print("Loading environment variables...")
load_dotenv(override=True)  # Force reload environment variables

# Initialize Flask app
app = Flask(__name__)
# Configure CORS for all origins in development and ngrok
CORS(app, resources={r"/*": {"origins": "*"}})

# Constants for validation
MAX_URL_LENGTH = 2000
MIN_QUESTIONS = 1
MAX_QUESTIONS = 20
SUPPORTED_LANGUAGES = ['en', 'hi']

# Database initialization
def init_db():
    conn = sqlite3.connect('quizzes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id TEXT PRIMARY KEY,
            youtube_url TEXT,
            questions TEXT,
            language TEXT,
            created_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
with app.app_context():
    init_db()

# Database connection management
def get_db_connection():
    """Get a database connection with retry mechanism"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect('quizzes.db', timeout=20)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)

def close_db_connection(conn):
    """Safely close database connection"""
    if conn:
        try:
            conn.close()
        except Exception as e:
            app.logger.error(f"Error closing database connection: {str(e)}")

# Configure OpenAI
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key not found in environment variables")

print(f"API Key found: {'Yes' if api_key else 'No'}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"Loaded API key: {api_key[:10]}...{api_key[-4:]}")
openai.api_key = api_key

def get_base_url():
    """Get the base URL for the application."""
    if 'BASE_URL' in app.config:
        return app.config['BASE_URL']
    elif 'BASE_URL' in os.environ:
        return os.environ['BASE_URL']
    return request.url_root.rstrip('/')

def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    try:
        print(f"Attempting to extract YouTube ID from: {url}")
        parsed_url = urlparse(url)
        
        if 'youtube.com' in parsed_url.netloc:
            query_params = parse_qs(parsed_url.query)
            video_id = query_params.get('v', [None])[0]
        elif 'youtu.be' in parsed_url.netloc:
            video_id = parsed_url.path.lstrip('/')
        else:
            print("Not a YouTube URL")
            return None
            
        if video_id:
            print(f"Successfully extracted YouTube ID: {video_id}")
        else:
            print("Could not find video ID in URL")
        return video_id
        
    except Exception as e:
        print(f"Error extracting YouTube ID: {str(e)}")
        return None

def get_youtube_transcript(video_id, preferred_lang='en'):
    """Get transcript of YouTube video"""
    try:
        if not video_id:
            print("No video ID provided")
            return None
            
        print(f"Fetching transcript for video ID: {video_id}")
        try:
            # List available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            print(f"Preferred language: {preferred_lang}")
            
            # Try to get transcripts in order of preference
            transcript = None
            try:
                if preferred_lang == 'hi':
                    # Try Hindi transcripts first
                    try:
                        transcript = transcript_list.find_transcript(['hi'])
                        print("Found manual Hindi transcript")
                    except:
                        try:
                            transcript = transcript_list.find_generated_transcript(['hi'])
                            print("Found auto-generated Hindi transcript")
                        except:
                            # If no Hindi transcript, try to translate to Hindi
                            try:
                                transcript = transcript_list.find_manually_created_transcript()
                                transcript = transcript.translate('hi')
                                print("Translated transcript to Hindi")
                            except:
                                print("Could not find or translate to Hindi")
                else:
                    # Try English transcripts
                    for lang_code in ['en-US', 'en-GB', 'en']:
                        try:
                            transcript = transcript_list.find_transcript([lang_code])
                            print(f"Found manual transcript in {lang_code}")
                            break
                        except:
                            continue
                    
                    # If no manual English transcript found, try auto-generated
                    if not transcript:
                        transcript = transcript_list.find_generated_transcript(['en'])
                        print("Found auto-generated English transcript")
                
            except Exception as e:
                print(f"Error finding transcript: {str(e)}")
                # Try to get any manual transcript and translate it to preferred language
                try:
                    transcript = transcript_list.find_manually_created_transcript()
                    transcript = transcript.translate(preferred_lang)
                    print(f"Found and translated manual transcript to {preferred_lang}")
                except:
                    print("Could not find or translate any transcript")
                    return None
            
            # Fetch the transcript
            transcript_list = transcript.fetch()
            print(f"Successfully fetched transcript with {len(transcript_list)} segments")
            
        except Exception as e:
            print(f"Error getting transcripts: {str(e)}")
            traceback.print_exc()  # Print full traceback
            return None
            
        if not transcript_list:
            print("No transcript found")
            return None
            
        print(f"Found {len(transcript_list)} transcript segments")
        
        # Process transcript segments
        processed_segments = []
        current_sentence = []
        
        for segment in transcript_list:
            text = segment['text'].strip()
            if not text:
                continue
                
            # Clean up text
            text = re.sub(r'\[.*?\]', '', text)  # Remove [Music] etc.
            text = re.sub(r'\(.*?\)', '', text)  # Remove (applause) etc.
            text = text.replace('\n', ' ')  # Replace newlines with spaces
            text = ' '.join(text.split())  # Normalize whitespace
            
            if not text:
                continue
                
            # Add to current sentence
            current_sentence.append(text)
            
            # If segment ends with sentence-ending punctuation, join and add to processed segments
            if text[-1] in '.!?':
                processed_segments.append(' '.join(current_sentence))
                current_sentence = []
        
        # Add any remaining text
        if current_sentence:
            processed_segments.append(' '.join(current_sentence))
        
        # Join all segments with proper spacing
        full_text = ' '.join(processed_segments)
        
        print(f"Successfully processed transcript of length: {len(full_text)}")
        print(f"Sample of processed text: {full_text[:200]}...")
        return full_text
        
    except Exception as e:
        print(f"Error getting YouTube transcript: {str(e)}")
        traceback.print_exc()  # Print full traceback
        return None

def extract_content(url):
    """Extract content from URL based on type"""
    try:
        print(f"\n=== Content Extraction ===")
        print(f"URL: {url}")
        
        if not url:
            raise ValueError("No URL provided")
        
        # Check if it's a YouTube video
        video_id = extract_youtube_id(url)
        if video_id:
            print("YouTube video detected")
            transcript = get_youtube_transcript(video_id, preferred_lang=request.json.get('language', 'en'))
            if transcript:
                print("Successfully extracted YouTube transcript")
                return transcript
            else:
                raise Exception("Could not extract YouTube transcript")

        # For other URLs, try to extract text content
        print("Attempting to fetch webpage content...")
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        
        print("Parsing webpage content...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        if not text:
            raise Exception("No content could be extracted from the URL")
            
        print(f"Successfully extracted webpage content (length: {len(text)})")
        return text

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {str(e)}")
        raise Exception(f"Could not fetch URL: {str(e)}")
    except Exception as e:
        print(f"Error in extract_content: {str(e)}")
        raise Exception(f"Content extraction failed: {str(e)}")

def generate_quiz_questions(content, num_questions=5):
    """Generate quiz questions using OpenAI GPT"""
    try:
        print(f"Generating quiz with {num_questions} questions...")
        
        # Initialize the OpenAI client
        client = openai.OpenAI()
        
        # Updated prompt to request correct answers and explanations
        messages = [
            {"role": "system", "content": "You are a helpful quiz generator. Generate quiz questions with correct answers and explanations."},
            {"role": "user", "content": f"""Generate {num_questions} multiple choice questions based on this content: {content}
            For each question:
            1. Start with the question number (e.g., '1.')
            2. List 4 options labeled A) through D)
            3. After the options, add 'Correct: X)' where X is the correct option letter
            4. Add 'Explanation: ' followed by a brief explanation of why that answer is correct"""}
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )

        quiz_text = response.choices[0].message.content
        print(f"Generated quiz text: {quiz_text}")

        # Parse the quiz text into a structured format
        questions = []
        current_question = None
        
        for line in quiz_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check for question number at start of line (1., 2., etc.)
            if re.match(r'^\d+\.', line):
                if current_question:
                    questions.append(current_question)
                current_question = {
                    'question': line.split('.', 1)[1].strip(),
                    'options': [],
                    'correct_answer': None,
                    'explanation': None
                }
            # Check for options (A), B), etc.)
            elif current_question and re.match(r'^[A-D]\)', line):
                current_question['options'].append(line)
            # Check for correct answer
            elif current_question and line.lower().startswith('correct:'):
                current_question['correct_answer'] = line.split(':', 1)[1].strip()
            # Check for explanation
            elif current_question and line.lower().startswith('explanation:'):
                current_question['explanation'] = line.split(':', 1)[1].strip()
                
        if current_question:
            questions.append(current_question)
            
        if not questions:
            print(f"Raw quiz text: {quiz_text}")
            raise Exception("Failed to generate valid quiz format")
            
        return questions
            
    except Exception as e:
        print(f"Error in generate_quiz: {str(e)}")
        raise e

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_quiz', methods=['POST'])
def handle_generate_quiz():
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        # Input validation
        video_url = data.get('video_url')
        if not video_url:
            return jsonify({'success': False, 'error': 'Video URL is required'}), 400
        if len(video_url) > MAX_URL_LENGTH:
            return jsonify({'success': False, 'error': 'URL is too long'}), 400
            
        num_questions = int(data.get('num_questions', 5))
        if not MIN_QUESTIONS <= num_questions <= MAX_QUESTIONS:
            return jsonify({'success': False, 
                          'error': f'Number of questions must be between {MIN_QUESTIONS} and {MAX_QUESTIONS}'}), 400
            
        language = data.get('language', 'en')
        if language not in SUPPORTED_LANGUAGES:
            return jsonify({'success': False, 
                          'error': f'Unsupported language. Supported languages are: {", ".join(SUPPORTED_LANGUAGES)}'}), 400
        
        # Extract content from the video
        try:
            content = extract_content(video_url)
            if not content:
                return jsonify({'success': False, 'error': 'Failed to extract content from URL'}), 400
        except Exception as e:
            app.logger.error(f"Content extraction error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to extract content. Please check the URL and try again.'
            }), 400
        
        # Generate quiz questions
        try:
            questions = generate_quiz_questions(content, num_questions)
            if not questions:
                return jsonify({'success': False, 'error': 'Failed to generate questions'}), 400
        except Exception as e:
            app.logger.error(f"Quiz generation error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to generate quiz. Please try again.'
            }), 400
            
        # Generate a unique ID for the quiz
        quiz_id = str(uuid.uuid4())
        
        # Store in database with proper connection management
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO quizzes (id, youtube_url, questions, language, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (quiz_id, video_url, json.dumps(questions), language, datetime.now()))
        conn.commit()
        
        # Get the base URL and create share URL
        base_url = get_base_url()
        share_url = f"{base_url}/quiz/{quiz_id}"
        
        return jsonify({
            'success': True,
            'quiz_id': quiz_id,
            'share_url': share_url,
            'questions': questions
        })
        
    except Exception as e:
        app.logger.error(f"Error in generate_quiz route: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }), 500
    finally:
        close_db_connection(conn)

@app.route('/quiz/<quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    try:
        conn = sqlite3.connect('quizzes.db')
        c = conn.cursor()
        c.execute('SELECT youtube_url, questions, language FROM quizzes WHERE id = ?', (quiz_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return jsonify({"error": "Quiz not found"}), 404
            
        youtube_url, questions_json, language = result
        
        # Parse questions JSON
        try:
            questions = json.loads(questions_json) if isinstance(questions_json, str) else questions_json
            
            # Ensure questions is a list
            if not isinstance(questions, list):
                return jsonify({"error": "Invalid quiz format"}), 500
                
            # Add index0 for each question (used in template)
            for i, q in enumerate(questions):
                q['index0'] = i
                
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing quiz data: {str(e)}")
            return jsonify({"error": "Invalid quiz data"}), 500
        
        return render_template(
            'quiz.html',
            youtube_url=youtube_url,
            questions=questions,
            quiz_id=quiz_id,
            language=language
        )
        
    except Exception as e:
        print(f"Error retrieving quiz: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/test_api')
def test_api():
    try:
        print("\nTesting API key...")
        print(f"Current OpenAI API Key: {openai.api_key[:10]}...{openai.api_key[-4:]}")
        
        # Initialize the OpenAI client
        client = openai.OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ]
        )
        
        test_response = response.choices[0].message.content
        print(f"OpenAI API Response: {test_response}")
        
        return jsonify({
            'success': True,
            'message': test_response
        })
        
    except Exception as e:
        print(f"API Test Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    print("Starting Flask application...")
    print(f"OpenAI API Key configured: {'Yes' if openai.api_key else 'No'}")
    app.run(debug=True, port=5004)
