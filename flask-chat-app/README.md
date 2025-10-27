# InsightChat - AI Chat Application with RAG

A clean, simple Flask-based chat application that integrates with Ollama for AI conversations and supports optional RAG (Retrieval Augmented Generation) for enhanced context.

## Project Structure

```
flask-chat-app
├── src
│   ├── app.py                # Main entry point of the Flask application
│   ├── chat
│   │   ├── __init__.py       # Initializes the chat module
│   │   ├── routes.py         # Defines chat-related routes
│   │   └── utils.py          # Utility functions for chat functionality
│   ├── config
│   │   └── __init__.py       # Initializes the configuration module
│   └── static
│       ├── css
│       │   └── style.css      # CSS styles for the chat interface
│       ├── js
│       │   └── chat.js        # JavaScript code for chat functionality
│       └── uploads            # Directory for storing uploaded files
├── templates
│   ├── base.html             # Base template for the application
│   ├── chat.html             # Main template for the chat interface
│   └── components
│       └── message.html      # Template for individual chat messages
├── requirements.txt          # Lists dependencies for the application
├── .env.example              # Example environment variables
├── .gitignore                # Specifies files to ignore in Git
└── README.md                 # Documentation for the project
```

## Installation

1. Clone the repository:

   ```
   git clone <repository-url>
   cd flask-chat-app
   ```

2. Create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables by copying `.env.example` to `.env` and updating the values as needed.

## Running the Application

To run the application, execute the following command:

```
python src/app.py
```

The application will start on `http://127.0.0.1:5000`. You can access it through your web browser.

## Usage

Once the application is running, you can interact with the chat interface by sending messages. The application supports image uploads, and keywords can be extracted from the uploaded images.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
