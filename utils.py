from functools import wraps
from flask import flash, redirect, url_for, render_template
from flask_login import current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Message

def email_confirmed_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Decorator to check if a user's email is confirmed.

        This decorator checks if the currently logged-in user has confirmed their email address.
        If the email is not confirmed, it flashes a message and redirects the user to the 'unconfirmed' route.
        Otherwise, it simply executes the decorated function.

        Args:
            f (function): The function to be decorated.

        Returns:
            function: The decorated function.
        """

        if current_user.is_authenticated and not current_user.email_confirmed:

            flash('Please confirm your email address.', 'danger')
            return redirect(url_for('unconfirmed'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def send_confirmation_email(mail, app, email):
    """
    Send a confirmation email to a user.

    This function generates a confirmation token and URL, then composes an email message with the 
    confirmation URL and sends it to the provided email address.

    Args:
        mail (Mail object): A Flask-Mail instance for sending emails.
        app (Flask application): The current Flask application.
        email (str): The email address to send the confirmation email to.
    """

    token = generate_confirmation_token(app, email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('/users/activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    msg = Message(subject, recipients=[email], html=html)
    mail.send(msg)

def send_reset_email(mail, app, email):
    """
    Send a password reset email to a user.

    This function generates a reset token and URL, then composes an email message with the 
    reset URL and sends it to the provided email address.

    Args:
        mail (Mail object): A Flask-Mail instance for sending emails.
        app (Flask application): The current Flask application.
        email (str): The email address to send the confirmation email to.
    """

    token = generate_confirmation_token(app, email)
    reset_url = url_for('password_reset', token=token, _external=True)
    html = render_template('/users/activate.html', reset_url=reset_url)
    subject = "A password reset was requested."
    msg = Message(subject, recipients=[email], html=html)
    mail.send(msg)

def generate_confirmation_token(app, email):
    """
    Generate an email confirmation token.

    This function uses the secret key from the application configuration to generate a URL-safe
    timed serialization of the provided email address.

    Args:
        app (Flask application): The current Flask application.
        email (str): The email address to generate a confirmation token for.

    Returns:
        str: The generated confirmation token.
    """

    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(app, token, expiration=3600):
    """
    Confirm a provided token.

    This function tries to decode the provided token using the secret key from the application configuration. 
    If the token is expired, it returns False. Otherwise, it returns the email address that was encoded in the token.

    Args:
        app (Flask application): The current Flask application.
        token (str): The token to confirm.
        expiration (int, optional): The maximum age of the token in seconds. Defaults to 3600.

    Returns:
        str or bool: The email address encoded in the token if it is valid, or False if the token is expired.
    """

    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )

    except SignatureExpired:
        return False
    
    return email