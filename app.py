from flask import(
    Flask, render_template, 
    request, redirect, 
    session, flash, url_for
)
from helpers import(
    calculate_bmi_and_category, calculate_healthy_weight_range, 
    create_weight_plot, create_bmi_plot, calculate_weight_difference,
    calculate_daily_water_intake, login_required, 
    calculate_healthy_weight_range, validate_confirmation_password, 
    validate_contact_inputs, validate_email, 
    validate_password, validate_username
)
from activity_validations import(
    validate_activity_type, validate_age, 
    validate_body_fat_percentage, validate_duration, 
    validate_exercise_heart_rate, validate_gender, 
    validate_height, validate_intensity, 
    validate_muscle_mass, validate_resting_heart_rate, 
    validate_water_intake, validate_weight
)

from dotenv import load_dotenv
from models import User, Workout, Article, Activity, Contact
from sqlalchemy.exc import SQLAlchemyError

from db import db
from flask_migrate import Migrate

load_dotenv()

app = Flask(__name__)
app.config.from_object("config.Config")

db.init_app(app)
migrate = Migrate(app, db)


# Number of articles to display per page
ARTICLES_PER_PAGE = 6

# Number of workouts to display per page
WORKOUTS_PER_PAGE = 8


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    if request.method == "POST":
        # Get login form input data
        username_or_email = request.form.get("username").lower()
        password = request.form.get("password")

        # List to store error messages
        messages = []

        # Ensure username was submitted
        if not username_or_email:
            messages.append(("danger", "Username or email is required"))

        # Ensure password was submitted
        elif not password:
            messages.append(("danger", "Password is required"))

        if not messages:
            # Check if the username or email exists in the database
            user = User.query.filter(
                (User.username == username_or_email) | (User.email == username_or_email)
            ).first()
            
            # Check if the query returned a valid user and valid password
            if not user or not user.check_password(password):
                messages.append(("danger", "Invalid username, email, and/or password"))

        if messages:
            # Flash the error messages
            for error in messages:
                flash(error)
            return render_template("login.html", messages=messages, username_or_email=username_or_email)

        # Remember which user has logged in
        session["user_id"] = user.id
        session["user_username"] = user.username

        # Check if the "Remember Me" checkbox is checked
        remember_me = request.form.get("remember")

        # Set the permanent session cookie to True if "Remember Me" is checked
        if remember_me:
            session.permanent = True

        # Redirect user to the home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Get the register form input data
        username = request.form.get("username").lower()
        email = request.form.get("email").lower()
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # List to store error messages
        messages = []

        # Check if username already exists
        existing_username = User.query.filter_by(username=username).first()

        if existing_username:
            messages.append(("danger", "Username already taken."))

        # Username validation
        validate_username(username, messages)

        # Check if email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            messages.append(("danger", "Email already registered."))

        # Email validation
        validate_email(email, messages)

        # Password validation
        validate_password(password, messages)

        # Confirmation password validation
        validate_confirmation_password(password, confirmation, messages)

        if messages:
            # Flash the error messages
            for error in messages:
                flash(error)
            return render_template(
                "register.html", messages=messages, 
                username=username, email=email
            )
        else:
            # Create and insert the new user into the database
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            # Get the newly registered user's ID
            new_user = User.query.filter_by(username=username).first()

            if new_user:
                # Store the ID of the newly registered user in the session for automatic login
                session["user_id"] = new_user.id
                session["user_username"] = new_user.username

                messages.append(("success", "Account successfully created."))
                flash(messages[-1])

                # Redirect the user to the home page
                return redirect("/")
            else:
                messages.append(
                    ("danger", "An error occurred while creating your account. Please try again.")
                )

                flash(messages[-1])

                return render_template(
                    "register.html", messages=messages, 
                    username=username, email=email
                )
    else:
        return render_template("register.html")


@app.route("/account")
@login_required
def account():
    # Get the logged-in user from the session
    user_id = session.get("user_id")

    # Fetch the user from the database using the ORM
    user = User.query.get(user_id)

    if not user:
        return flash("danger", "User not found")

    return render_template('account.html', user=user)



@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    # Get the change password form input data
    user_id = session.get("user_id")

    # List to store error messages
    messages = []

    if not user_id:
        messages.append(("danger", "User not found."))
        flash(messages[-1])
        return redirect("/")

    if request.method == 'POST':
        # Handle the password change form submission
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirmation = request.form.get('confirmation')

        # Fetch the user from the database using the ORM
        user = User.query.get(user_id)

        if not user:
            messages.append(("danger", "User not found."))
        elif not user.check_password(current_password):
            messages.append(("danger", "Current password is incorrect."))
        else:
            # Check if new password and confirmation are valid
            if not new_password:
                messages.append(("danger", "New Password is required."))
            else:
                validate_password(new_password, messages)
                if new_password == current_password:
                    messages.append(("danger", "New password must be different from the current password."))

            # Ensure the new password and confirmation match
            validate_confirmation_password(new_password, confirmation, messages)

            if not messages:
                # Update the user's password
                user.set_password(new_password)
                db.session.commit()
                messages.append(("success", "Password successfully changed."))

                # Flash the success message
                flash(messages[-1])

                # Redirect the user to the home page
                return redirect("/")

        # Flash the error messages
        for error in messages:
            flash(error)

    return render_template('change_password.html')



@app.route('/workouts')
def workouts():
    # Get the current page number from the query string, defaulting to 1
    page = int(request.args.get('page', 1))
    # Get the selected category from the query string
    selected_category = request.args.get('category')

    # Define the query for retrieving workouts
    query = Workout.query
    if selected_category:
        query = query.filter_by(category=selected_category)

    # Get the total number of workouts based on the selected category
    total_workouts = query.count()
    # Calculate the total number of pages
    total_pages = (total_workouts + WORKOUTS_PER_PAGE - 1) // WORKOUTS_PER_PAGE

    # Get the workouts for the current page
    workouts = query.paginate(page=page, per_page=WORKOUTS_PER_PAGE, error_out=False).items

    # Get all distinct workout categories from the database
    all_categories = db.session.query(Workout.category).distinct().all()
    categories = [category[0] for category in all_categories]

    # Convert workouts to a list of dictionaries
    workout_data = [{
        'name': workout.name,
        'description': workout.description,
        'image_path': workout.image_path,
        'category': workout.category
    } for workout in workouts]

    return render_template(
        'workouts.html',
        workout_data=workout_data,
        categories=categories,
        pagination=page,
        total_pages=total_pages,
        total_workouts=total_workouts
    )


@app.route('/articles')
def articles():
    # Get the page number from the URL query parameters, defaulting to 1
    page = request.args.get('page', 1, type=int)

    # Query the articles from the database, ordered by created_at in descending order, and paginate the results
    pagination = Article.query.order_by(
        Article.created_at.desc()).paginate(page=page, per_page=ARTICLES_PER_PAGE, error_out=False
    )
    articles = pagination.items

    # Get the total number of articles in the database
    total_articles = pagination.total

    return render_template(
        'articles.html',
        articles=articles,
        pagination=page,
        total_articles=total_articles,
        ARTICLES_PER_PAGE=ARTICLES_PER_PAGE
    )


@app.route('/article/<int:article_id>')
def show_article(article_id):
    # Fetch the article by its ID using SQLAlchemy ORM
    article = Article.query.get(article_id)

    # If the article is not found, flash a message and render the details page with an error
    if not article:
        flash("Article not found", "danger")
        return render_template('article_details.html')
    
    # Split the content into paragraphs using '|' as the delimiter
    paragraphs = article.content.split('|')

    # Format the created_at attribute to a string representing the date
    created_at = article.created_at.strftime("%Y-%m-%d")

    return render_template(
        'article_details.html', article=article, 
        paragraphs=paragraphs, created_at=created_at
    )


@app.route('/activity', methods=['GET', 'POST'])
@login_required
def activity():
    # Get the logged-in user from the session
    user_id = session.get("user_id")

    # List to store error messages
    messages = []

    if not user_id:
        messages.append(("danger", "User not found."))

    if request.method == 'POST':
        # Get the activity form inputs
        age = request.form.get('age')
        gender = request.form.get('gender')
        weight = request.form.get('weight')
        height = request.form.get('height')
        activity_type = request.form.get('activityType')
        duration = request.form.get('duration')
        intensity = request.form.get('intensity')
        resting_heart_rate = request.form.get('restingHeartRate')
        exercise_heart_rate = request.form.get('exerciseHeartRate')
        body_fat_percentage = request.form.get('bodyFatPercentage')
        muscle_mass = request.form.get('muscleMass')
        water_intake = request.form.get('waterIntake')

        # Input validations
        if not age:
            messages.append(("danger", "Age is required."))
        else:
            age, messages = validate_age(age, messages)

        validate_gender(gender, messages)

        if not weight:
            messages.append(("danger", "Weight is required."))
        else:
            weight, messages = validate_weight(weight, messages)

        if not height:
            messages.append(("danger", "Height is required."))
        else:
            height, messages = validate_height(height, messages)

        validate_activity_type(activity_type, messages)

        if not duration:
            messages.append(("danger", "Duration is required."))
        else:
            duration, messages = validate_duration(duration, messages)

        validate_intensity(intensity, messages)

        if not resting_heart_rate:
            messages.append(("danger", "Resting Heart Rate is required."))
        else:
            resting_heart_rate, messages = validate_resting_heart_rate(resting_heart_rate, messages)

        if not exercise_heart_rate:
            messages.append(("danger", "Exercise Heart Rate is required."))
        else:
            exercise_heart_rate, messages = validate_exercise_heart_rate(exercise_heart_rate, messages)

        if not body_fat_percentage:
            messages.append(("danger", "Body Fat Percentage is required."))
        else:
            body_fat_percentage, messages = validate_body_fat_percentage(body_fat_percentage, messages)

        if not muscle_mass:
            messages.append(("danger", "Muscle Mass is required."))
        else:
            muscle_mass, messages = validate_muscle_mass(muscle_mass, messages)

        if not water_intake:
            messages.append(("danger", "Water Intake is required."))
        else:
            water_intake, messages = validate_water_intake(water_intake, messages)

        if not messages:
            try:
                # Create a new Activity object
                new_activity = Activity(
                    user_id=user_id,
                    age=age,
                    gender=gender,
                    weight=weight,
                    height=height,
                    activity_type=activity_type,
                    duration=duration,
                    intensity=intensity,
                    resting_heart_rate=resting_heart_rate,
                    exercise_heart_rate=exercise_heart_rate,
                    body_fat_percentage=body_fat_percentage,
                    muscle_mass=muscle_mass,
                    water_intake=water_intake
                )

                # Add the new activity to the session and commit
                db.session.add(new_activity)
                db.session.commit()

                messages.append(("success", "Activity successfully added."))

                # Flash the success message
                flash(messages[-1])

                # Redirect to the /stats route
                return redirect(url_for('stats'))

            except SQLAlchemyError as e:
                db.session.rollback()
                messages.append(("danger", "An error occurred while adding the activity. Please try again."))

        # Flash the error messages
        for error in messages:
            flash(error)

        return render_template(
            'user_activity.html', messages=messages, 
            age=age, gender=gender, 
            weight=weight, height=height, 
            activity_type=activity_type, duration=duration, 
            intensity=intensity, resting_heart_rate=resting_heart_rate, 
            exercise_heart_rate=exercise_heart_rate,
            body_fat_percentage=body_fat_percentage, muscle_mass=muscle_mass, 
            water_intake=water_intake
        )
    else:
        return render_template('user_activity.html')


@app.route('/stats', methods=['GET'])
@login_required
def stats():
    # Get the logged-in user's ID
    user_id = session.get("user_id")
    stats_data = []

    if not user_id:
        stats_data = None
        return render_template('stats.html', stats=stats_data)

    # Fetch distinct user activity data
    distinct_user_activity_data = (
        db.session.query(Activity).
        filter_by(user_id=user_id)
        .distinct().all()
    )

    # Fetch the latest user activity
    latest_user_activity = (
        db.session.query(Activity)
        .filter_by(user_id=user_id)
        .order_by(Activity.registered_at.desc())
        .first()
    )

    # Fetch all user activities
    user_activities = db.session.query(Activity).filter_by(user_id=user_id).all()

    # Fetch all user activities sorted by registered_at in descending order
    user_activities_sorted = (
        db.session.query(Activity)
        .filter_by(user_id=user_id)
        .order_by(Activity.registered_at.desc())
        .all()
    )

    if (
        not distinct_user_activity_data or 
        not latest_user_activity or 
        not user_activities or 
        not user_activities_sorted
    ):
        stats_data = None
        return render_template('stats.html', stats=stats_data)

    age = distinct_user_activity_data[0].age if distinct_user_activity_data else None
    gender = distinct_user_activity_data[0].gender if distinct_user_activity_data else None
    body_fat_percentage = latest_user_activity.body_fat_percentage if latest_user_activity else None
    muscle_mass = latest_user_activity.muscle_mass if latest_user_activity else None
    weight_kg = latest_user_activity.weight if latest_user_activity else None
    height_cm = latest_user_activity.height if latest_user_activity else None

    # Calculate healthy weight range
    if height_cm is not None:
        healthy_weight_range_result = calculate_healthy_weight_range(height_cm)
    else:
        healthy_weight_range_result = None

    if healthy_weight_range_result:
        healthy_weight_range_str = "{:.1f}kg - {:.1f}kg".format(*healthy_weight_range_result)
    else:
        healthy_weight_range_str = None
        stats_data = None

    daily_water_intake = calculate_daily_water_intake(latest_user_activity)
    user_water_intake = latest_user_activity.water_intake if latest_user_activity else None
    weight_difference = calculate_weight_difference(user_activities_sorted)
    weight_plot_data = create_weight_plot(user_activities)
    bmi, bmi_category_result = calculate_bmi_and_category(weight_kg, height_cm)
    bmi_plot_data = create_bmi_plot(user_activities)

    if not weight_plot_data or not bmi_plot_data:
        return render_template('stats.html', stats=None)

    stats_data.append({'index': 0, 'graph_data': weight_plot_data})
    stats_data.append({'index': 1, 'graph_data': bmi_plot_data})

    # Convert activities to a list of dictionaries
    activities = []
    for activity in user_activities_sorted:
        activity_data = {
            "activity_type": activity.activity_type.capitalize(),
            "duration": activity.duration,
            "intensity": activity.intensity.capitalize(),
            "resting_heart_rate": activity.resting_heart_rate,
            "exercise_heart_rate": activity.exercise_heart_rate,
            "registered_at": activity.registered_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        activities.append(activity_data)

    return render_template(
        'stats.html', stats=stats_data, 
        age=age, gender=gender, 
        body_fat_percentage=body_fat_percentage, 
        muscle_mass=muscle_mass, weight=weight_kg, 
        height=height_cm, bmi=bmi, 
        bmi_category=bmi_category_result, 
        healthy_weight_range=healthy_weight_range_str, 
        weight_difference=weight_difference, 
        daily_water_intake=daily_water_intake, 
        user_water_intake=user_water_intake, activities=activities
    )


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name'].capitalize()
        email = request.form['email']
        subject = request.form['subject'].capitalize()
        phone = request.form['phone']
        message = request.form['message'].capitalize()

        messages = []

        # Assuming these functions validate the inputs and add error messages if needed
        validate_contact_inputs(name, "Name", messages)
        validate_email(email, messages)
        validate_contact_inputs(subject, "Subject", messages)
        validate_contact_inputs(phone, "Phone", messages)
        validate_contact_inputs(message, "Message", messages)

        if not messages:
            try:
                # Create a new Contact instance
                new_contact = Contact(
                    name=name,
                    email=email,
                    subject=subject,
                    phone=phone,
                    message=message
                )
                
                # Add the new contact to the session and commit to the database
                db.session.add(new_contact)
                db.session.commit()

                messages.append(("success", "Thank you for your message!"))
                flash(messages[-1])

                # Redirect the user to the home page
                return redirect("/")

            except Exception as e:
                # Handle any errors that occur during the database transaction
                db.session.rollback()
                messages.append(("danger", "There was a problem submitting your message. Please try again!"))
                flash(messages[-1])
                return render_template(
                    'contact.html', messages=messages, name=name, 
                    email=email, subject=subject, 
                    phone=phone, message=message
                )

        else:
            # Flash the error messages
            for error in messages:
                flash(error)
            return render_template(
                'contact.html', messages=messages, name=name, 
                email=email, subject=subject, 
                phone=phone, message=message
            )

    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)