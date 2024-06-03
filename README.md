# Movie Playlist App

A web application to create and manage movie playlists using Flask and Firebase.

## Features

- User authentication with Firebase
- Movie search using OMDB API
- Create and manage playlists
- Public and private playlists

## Requirements

- Python 3.8+
- Flask
- Firebase Admin SDK
- Requests
- python-dotenv

## Setup

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the project root directory and add the following variables:
    ```
    FLASK_SECRET_KEY=your_secret_key
    FIREBASE_KEY_JSON=your_firebase_credentials_json
    ```

5. Run the application:
    ```sh
    python app.py
    ```

## Deployment

This application can be deployed on platforms like  Vercel. Ensure you set the required environment variables on the platform you are deploying.

## License

This project is licensed under the MIT License.
