# Quiz Generator

A web application that generates quizzes based on content from URLs. It can analyze various types of content including YouTube videos, blog posts, and documents to create interactive multiple-choice quizzes.

## Features

- Generate quizzes from any URL (YouTube videos, blog posts, articles)
- Customizable number of questions (5, 7, or 10)
- Multiple-choice questions with explanations
- Modern, responsive UI
- Instant feedback on quiz answers

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Enter a URL containing the content you want to create a quiz from
2. Select the number of questions you want (5, 7, or 10)
3. Click "Generate Quiz"
4. Answer the questions and click "Check Answers" to see your results

## Supported Content Types

- YouTube videos (automatically extracts transcripts)
- Blog posts and articles
- Text documents

## Technologies Used

- Backend: Flask (Python)
- Frontend: HTML, JavaScript, Tailwind CSS
- AI: OpenAI GPT-3.5 for content analysis and quiz generation
- Additional libraries: BeautifulSoup4, youtube-transcript-api
