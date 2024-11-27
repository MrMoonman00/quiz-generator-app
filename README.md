<<<<<<< HEAD
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
=======
# Quiz Generator App

## Overview
The Quiz Generator App is a tool designed to help users create and manage quizzes easily. It provides a user-friendly interface for creating questions, setting up quizzes, and tracking results.

## Features
- Create multiple-choice questions
- Organize quizzes into categories
- Track quiz results and performance
- User authentication and profile management

## Setup Instructions

### Prerequisites
- Node.js and npm installed on your machine
- Git installed on your machine

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/MrMoonman00/quiz-generator-app.git
   ```
2. Navigate to the project directory:
   ```bash
   cd quiz-generator-app
   ```
3. Install the dependencies:
   ```bash
   npm install
   ```

### Running the Application
1. Start the development server:
   ```bash
   npm start
   ```
2. Open your browser and go to `http://localhost:3000` to view the app.

### Building for Production
To create a production build, run:
```bash
npm run build
```

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License
This project is licensed under the MIT License.
>>>>>>> 98d5c8a (Add README.md with project details)
