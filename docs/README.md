https://platform.openai.com/docs/introduction

Capstone Project

This project, a web application built with the Flask framework, incorporates the OpenAI API to provide powerful AI functionalities.

Description

The Capstone project, titled "Interactive Storytelling with AI: A New Frontier in Children's Education," is designed to promote creativity, stimulate imagination, and bolster critical thinking among young readers. The primary users are children aged between 5 and 12 years, but educators and parents seeking innovative educational tools may also find it beneficial.

The AI model underpinning the application is trained on a vast array of children's stories, fables, and educational content, enabling it to generate a diverse range of interactive stories. It learns from anonymized user interaction data to personalize the storytelling experience further.

The platform includes user authentication, profile management, interactive storytelling sessions, story logging (to continue where left off), and story personalization features based on user preferences and interactions. Users can sign up, create a profile, select a story theme or start a new story, interact with the AI-generated narratives, and get a personalized story based on their inputs. They can save and resume stories anytime.

This project goes beyond simple CRUD operations by integrating advanced AI for personalized, real-time interactive storytelling. The AI's ability to learn from user interactions and continually evolve the storytelling experience is what sets this platform apart. A stretch goal is to incorporate multilingual support and implement features aligning with educational standards, turning the platform into a fun learning tool.

In terms of data security, the platform handles sensitive information, particularly user profiles and children's activity data. This information is anonymized and secured following the highest standards. The project uses Flask-SQLAlchemy to manage a database storing user profiles, story data (including generated stories and user interaction data), and user preferences.

Challenges anticipated with this project include data privacy, accuracy of story generation, adapting the AI responses to varied user inputs, and efficiently handling real-time interactions.

Installation

First, clone the repository to your local machine:

```bash
git clone https://github.com/tabrown76/Capstone.git
```
Next, navigate to the project directory and create a virtual environment:

```bash
cd Capstone
python3 -m venv venv
```
Activate the virtual environment:

On Windows, run:

```cmd
venv\Scripts\activate
```
On Unix or Linux, run:

```bash
source venv/bin/activate
```
Then install the required packages:

```bash
pip install -r requirements.txt
```
Usage

To run the application, execute the following command:

```bash
flask run
```
Then visit http://127.0.0.1:5000/ in your web browser.

Tools Used 

    Python: The project is written in Python.
    Flask: Flask is a micro web framework used for handling requests/responses.
    Flask-Bcrypt: Used for password hashing and checking.
    Flask-Login: Manages user sessions.
    Flask-SQLAlchemy: A Flask extension that provides SQLAlchemy support for database operations.
    Flask-WTF: Provides integration with WTForms for form handling and validation.
    SQLAlchemy: The Python SQL Toolkit and Object-Relational Mapper.
    OpenAI: The OpenAI API client library is used for AI functionalities.
    Gunicorn: A Python WSGI HTTP Server for UNIX.
    Jinja2: A full-featured template engine for Python.

Contributing

This is a work in progress. Feel free to email me your thoughts.

License

You will need a paid OpenAI API key.

Contact

For any questions, feel free to reach out to me at tabrown76@gmail.com