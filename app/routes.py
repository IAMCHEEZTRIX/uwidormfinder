import os
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app.models import Application, User, Room
from app import db

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    
    session.pop('_flashes', None)
    
    if request.method == 'POST':
        student_id = request.form.get('userID')
        password = request.form.get('password')
        
        user = User.query.filter_by(user_id = student_id).first()
        
        if user and check_password_hash(user.password, password):
            session['student_id'] = int(user.user_id)
            session['usertype'] = user.usertype
            
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid student ID or password.', 'danger')
    
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.pop('student_id', None)
    
    flash('You have been logged out.', 'info')
    return render_template('login.html')


@main.route('/dashboard', methods=['GET'])
def dashboard():
    if 'student_id' not in session:
        flash('Please log in to view your dashboard', 'danger')
        return redirect(url_for('main.login'))

    student_id = session['student_id']

    bookings = Application.query.filter_by(student_id=student_id).all()
    rooms = [Room.query.get(booking.room_id) for booking in bookings if booking.room_id]

    return render_template('dashboard.html', rooms=rooms)


@main.route('/create_account', methods = ['GET','POST'])
def create_account():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation logic
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('main.create_account'))

        existing_user = User.query.filter_by(user_id=student_id).first()
        if existing_user:
            flash('Student ID is already registered', 'danger')
            return redirect(url_for('main.create_account'))

        if User.query.filter_by(email=email).first():
            flash('Email is already registered', 'danger')
            return redirect(url_for('main.create_account'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(fname=first_name, lname=last_name, user_id=student_id, email=email, usertype='student', password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.login'))

    return render_template('create_account.html')


@main.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        pass
    return render_template('forgot_password.html')
    


    
    
@main.route('/room_search', methods=['GET','POST'])
def room_search():
    
    if session.get('usertype') != 'student':
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.dashboard'))
    
    rooms = []
    if request.method == 'POST':
        room_type = request.form.get('room_type')
        dormitory = request.form.get('dormitory')  
        level = request.form.get('level')  
        availability = request.form.get('availability')
        
        # Query the database based on the search criteria
        query = Room.query
        if room_type:
            query = query.filter_by(room_type=room_type)
            
        if dormitory:
            query = query.filter_by(building=int(dormitory))
               
        if level:
            query = query.filter_by(floor_number=int(level))   
            
        if availability == 'now':
            query = query.filter(Room.available_rooms > 0)
        
        print(query.statement.compile(dialect=db.engine.dialect, compile_kwargs={"literal_binds": True}))
            
        rooms = query.all()
    
    return render_template('room_search.html', rooms=rooms)


@main.route('/book_room/<int:room_id>/<string:action>', methods=['GET', 'POST'])
def book_room(room_id, action):
    
    if session.get('usertype') != 'student':
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.dashboard'))
    
    room = Room.query.get_or_404(room_id)
    
    if action == 'book':
        student = User.query.filter_by(user_id=session['student_id']).first()
        form_data = {
            'student_id': student.user_id if student else '',
            'first_name': student.fname if student else '',
            'last_name': student.lname if student else '',
            'email': student.email if student else '',  
            'action': action,
            'room_id':room_id
        }
        
    if action == 'edit':
        application = Application.query.filter_by(student_id=session['student_id'], room_id=int(room_id)).first()

        form_data = {
            'student_id': application.student_id if application else '',
            'first_name': application.first_name if application else '',
            'last_name': application.last_name if application else '',
            'middle_name': application.middle_name if application else '',
            'email': application.email if application else '',
            'telephone': application.telephone if application else '',
            'gender': application.gender if application else '',
            'educationLevel': application.education_level if application else '',
            'programType': application.program_type if application else '',
            'reason_for_applying': application.reason_for_applying if application else '',
            'co_curricular_activities': application.co_curricular_activities if application else '',
            'agreement': application.agreement if application else '',
            'action': action, 
            'room_id':room_id  
        }
        
    return render_template('book_room.html', room=room, errors={}, form_data=form_data)

@main.route('/submit_application', methods=['POST'])
def submit_application():
    errors = {}
    
    if request.method == 'POST':
        
        # Cannot book the same room more than one time
        room_id = int(request.form.get('room_id'))
        data = request.form
        application = Application.query.filter_by(student_id=session['student_id'], room_id=int(room_id)).first()
        if application:
            errors['room'] = 'You\'ve already booked the selected room'
        
        student_id = request.form.get('student_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        middle_name = request.form.get('middle_name')
        email = request.form.get('email')
        telephone = request.form.get('telephone')
        gender = request.form.get('gender')
        education_level = request.form.get('education_level')
        program_type = request.form.get('programType')
        reason_for_applying = request.form.get('reason_for_applying')
        co_curricular_activities = request.form.get('co_curricular_activities')
        agreement = True if request.form.get('agreement') else False
        
        # Validation
        if not student_id:
            errors['student_id'] = 'Student ID is required.'
        elif  not int(student_id) == session['student_id']:
            errors['student_id'] = 'You cannot book a room using a student ID different from the one you used to log in'
        
        
        if not first_name:
            errors['first_name'] = 'First Name is required.'

        if not last_name:
            errors['last_name'] = 'Last Name is required.'

        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email:  # Simple email validation
            errors['email'] = 'Enter a valid email address.'

        if not telephone:
            errors['telephone'] = 'Telephone number is required.'

        if not gender:
            errors['gender'] = 'Gender is required.'

        if not education_level:
            errors['education_level'] = 'Level of Education is required.'

        if not program_type:
            errors['program_type'] = 'Program Type is required.'

        if not reason_for_applying:
            errors['reason_for_applying'] = 'Reason for applying is required.'

        if not agreement:
            errors['agreement'] = 'You must accept the agreement.'

        # If errors exist, return the form with error messages
        if errors:
            room = Room.query.filter_by(id=room_id).first()
            return render_template('book_room.html', errors=errors, room=room, form_data=request.form)

        
        data = Application(
            student_id = request.form['student_id'],
            first_name = request.form['first_name'],
            last_name = request.form['last_name'],
            middle_name = request.form.get('middle_name'),
            email = request.form['email'],
            telephone = request.form['telephone'],
            gender = request.form['gender'],
            education_level = request.form['education_level'],
            program_type = request.form['programType'],
            reason_for_applying = request.form['reason_for_applying'],
            co_curricular_activities = request.form.get('co_curricular_activities'),
            agreement = True if request.form.get('agreement') else False,
            room_id = int(room_id),
            status = "Pending"
        )
        db.session.add(data)
        db.session.commit()
        
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    
@main.route('/edit_application/<int:room_id>', methods=['GET', 'POST'])
def edit_application(room_id):
    if session.get('usertype') != 'student':
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.dashboard'))
    
    application = Application.query.filter_by(student_id=session['student_id'], room_id=room_id).first()

    if not application:
        flash('Application not found.', 'danger')
        return redirect(url_for('main.dashboard.html'))

    if request.method == 'POST':
        # Update application attributes with data from the form
        application.first_name = request.form.get('first_name', application.first_name)
        application.last_name = request.form.get('last_name', application.last_name)
        application.middle_name = request.form.get('middle_name', application.middle_name)
        application.email = request.form.get('email', application.email)
        application.telephone = request.form.get('telephone', application.telephone)
        application.gender = request.form.get('gender', application.gender)
        application.education_level = request.form.get('educationLevel', application.education_level)
        application.program_type = request.form.get('programType', application.program_type)
        application.reason_for_applying = request.form.get('reason_for_applying', application.reason_for_applying)
        application.co_curricular_activities = request.form.get('co_curricular_activities', application.co_curricular_activities)
        application.agreement = request.form.get('agreement', application.agreement) == 'on'

        # Save changes to the database
        db.session.commit()
        flash('Application updated successfully.', 'success')
        return redirect(url_for('main.view_booking'))

    # Pre-fill the form with existing data
    form_data = {
        'student_id': application.student_id,
        'first_name': application.first_name,
        'last_name': application.last_name,
        'middle_name': application.middle_name,
        'email': application.email,
        'telephone': application.telephone,
        'gender': application.gender,
        'educationLevel': application.education_level,
        'programType': application.program_type,
        'reason_for_applying': application.reason_for_applying,
        'co_curricular_activities': application.co_curricular_activities,
        'agreement': application.agreement
    }

    return render_template('edit_application.html', form_data=form_data, room_id=room_id)

    
@main.route('/view_booking', methods=['GET'])
def view_booking():
    if session.get('usertype') != 'student':
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.dashboard'))
    
    if 'student_id' not in session:
        flash('Please log in to view your bookings', 'danger')
        return redirect(url_for('main.login'))

    student_id = session['student_id']

    bookings = Application.query.filter_by(student_id=student_id).all()
    rooms = [Room.query.get(booking.room_id) for booking in bookings if booking.room_id]

    return render_template('view_booking.html', rooms=rooms)

@main.route('/track_application', methods=['GET', 'POST'])
def track_application():
    statuses = ['Pending', 'Application Approved', 'Payment Under Review', 'Room Booked']

    room_id = request.args.get('room_id')
    student_id = session['student_id']

    if room_id:
        # Fetch the specific application by room_id and student_id
        application = Application.query.filter_by(room_id=room_id, student_id=student_id).first()
        if application:
            room = Room.query.get(application.room_id) if application.room_id else None
            applications_with_rooms = [
                {"application": application, "room": room}
            ]
        else:
            applications_with_rooms = []
    else:
        # Fetch all applications for the student
        applications = Application.query.filter_by(student_id=student_id).all()
        applications_with_rooms = [
            {
                "application": application,
                "room": Room.query.get(application.room_id) if application.room_id else None
            }
            for application in applications
        ]

    return render_template(
        'track_application.html',
        applications_with_rooms=applications_with_rooms,
        statuses=statuses,
        enumerate=enumerate
    )
    
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/upload_receipt/<int:application_id>', methods=['GET', 'POST'])
def upload_receipt(application_id):
    if session.get('usertype') != 'student':
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.dashboard'))
    
    session.pop('_flashes', None)
    
    if 'receipt' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('main.track_application'))

    file = request.files['receipt']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('main.track_application'))

    if file and allowed_file(file.filename):
        # Get the application and its details
        application = Application.query.get(application_id)
        if not application:
            flash('Application not found', 'danger')
            return redirect(url_for('main.track_application'))

        student_id = application.student_id
        room_id = application.room_id

        # Directory to save uploads
        upload_folder = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)  # Ensure the directory exists

        # Check if a previous receipt exists and delete it
        previous_receipt_prefix = f"Payment_receipt_{student_id}_{room_id}_{application_id}"
        for existing_file in os.listdir(upload_folder):
            if existing_file.startswith(previous_receipt_prefix):
                os.remove(os.path.join(upload_folder, existing_file))

        # Save the new file with a unique name
        filename = f"{previous_receipt_prefix}.{file.filename.rsplit('.', 1)[1].lower()}"
        filepath = os.path.join(upload_folder, secure_filename(filename))
        file.save(filepath)

        # Update application status
        application.status = 'Payment Under Review'
        db.session.commit()

         # Flash a success message specific to the application
        flash(f'Payment receipt uploaded successfully and is under review', f'success_{application_id}')
        return redirect(url_for('main.track_application', room_id=room_id))
    else:
        flash(f'Invalid file format for application {application_id}. Only PDF, JPG, and PNG are allowed.', 'danger')
        return redirect(url_for('main.track_application', room_id=application_id))
    
@main.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    errors = {}
    form_data = None
    return render_template('create_admin.html', errors = errors, form_data=form_data)
    
@main.route('/system_log', methods=['GET', 'POST'])
def system_log():
    pass