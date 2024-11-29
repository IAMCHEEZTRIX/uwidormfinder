import os
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from sqlalchemy import func, text
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app.models import Application, EmailTemplate, User, Room
from app import db
from flask_mail import Message
from app import mail 
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from secrets_info import SENDGRID_API_KEY

main = Blueprint('main', __name__)

def is_int_like(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def send_email(to_email, subject, content):
    message = Mail(
        from_email='damionedu@gmail.com',
        to_emails=to_email,
        subject=subject,
        html_content=content,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent! Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    
    # Check if there's an "unauthorized access" flash message and keep it
    flashes = session.get('_flashes', [])
    unauthorized_flash = any(flash for flash in flashes if flash[0] == 'Unauthorized access')

    # Clear flashes only if there is no "unauthorized access" message
    if not unauthorized_flash:
        session.pop('_flashes', None)
    
    if request.method == 'POST':
        student_id = request.form.get('userID')
        password = request.form.get('password')
        
        user = User.query.filter_by(user_id = student_id).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = int(user.user_id)
            session['usertype'] = user.usertype
            
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid student ID or password.', 'danger')
    
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.pop('student_id', None)
    session.pop('usertype', None)
    
    flash('You have been logged out.', 'info')
    return render_template('login.html')


@main.route('/dashboard', methods=['GET'])
def dashboard():
    
    if 'user_id' not in session:
        flash('Please log in to view your dashboard', 'danger')
        return redirect(url_for('main.login'))

    student_id = session['user_id']

    bookings = Application.query.filter_by(student_id=student_id).all()
    rooms = [Room.query.get(booking.room_id) for booking in bookings if booking.room_id]

    return render_template('dashboard.html', rooms=rooms)


@main.route('/create_account', methods = ['GET','POST'])
def create_account():
    errors = {}
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        middle_name = request.form.get('middle_name')
        email = request.form.get('email')
        telephone = request.form.get('telephone')
        gender = request.form.get('gender')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation data
        if not student_id:
            errors['student_id'] = 'Student ID is required'
        elif is_int_like(student_id):
            existing_user = User.query.filter_by(user_id=student_id).first()
            if existing_user:
                errors['student_id'] = 'Student ID is already registered'
        else:
            errors['student_id'] = 'Invalid Student ID, it should be an integer'
            
        if not first_name:
            errors['first_name'] = 'First Name is required'

        if not last_name:
            errors['last_name'] = 'Last Name is required'

        if not email:
            errors['email'] = 'Email is required'
        elif '@' not in email: 
            errors['email'] = 'Enter a valid email address'
        elif User.query.filter_by(email=email).first():
            errors['email'] = 'Email is already registered'
        if not telephone:
            errors['telephone'] = 'Telephone number is required'

        if not gender:
            errors['gender'] = 'Gender is required'
        
        if not password:
            errors['password'] = 'Password is required'
        elif not confirm_password:
            errors['confirm_password'] = 'Confirm Password is required' 
        elif password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'


        # If errors exist, return the form with error messages
        if errors:
            return render_template('create_account.html', errors=errors, form_data=request.form)

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User(
            fname = first_name, 
            lname = last_name, 
            middle_name = middle_name,
            user_id = student_id, 
            email = email, 
            telephone = telephone,
            usertype = 'student', 
            password = hashed_password
            
            )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.login'))

    return render_template('create_account.html', errors=errors, form_data={})

@main.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    errors = {}
    
    if session.get('usertype') != 'IT':
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':

        # Get form data
        staffid = request.form.get('staffid')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        middle_name = request.form.get('middle_name')
        email = request.form.get('email')
        telephone = request.form.get('telephone')
        gender = request.form.get('gender')
        
        # Validation data
        if not staffid:
            errors['staffid'] = 'Staff ID is required.'
        elif is_int_like(staffid):
            existing_user = User.query.filter_by(user_id=staffid).first()
            if existing_user:
                errors['staffid'] = 'Staff ID is already registered'
        else:
            errors['staffid'] = 'Invalid Staff ID, it should be an integer'
        
        if not first_name:
            errors['first_name'] = 'First Name is required.'

        if not last_name:
            errors['last_name'] = 'Last Name is required.'

        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email: 
            errors['email'] = 'Enter a valid email address.'

        if not telephone:
            errors['telephone'] = 'Telephone number is required.'

        if not gender:
            errors['gender'] = 'Gender is required.'
        

        # If errors exist, return the form with error messages
        if errors:
            return render_template('create_admin.html', errors=errors, form_data=request.form)

        # Create a user object with form data
        new_user = User(
            fname = first_name, 
            lname = last_name, 
            middle_name = middle_name, 
            user_id = staffid, 
            email = email, 
            telephone = telephone,
            usertype = 'Admin', 
            password = generate_password_hash('password', method='pbkdf2:sha256')
            
            )
        # Save user to the database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Admin account was successfully created!', 'success')
        
        return redirect(url_for('main.dashboard'))
    
    return render_template('create_admin.html', errors={}, form_data={})
    

@main.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        pass
    return render_template('forgot_password.html')
    
      
    
@main.route('/room_search', methods=['GET','POST'])
def room_search():
    
    if session.get('usertype') != 'student':
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.login'))
    
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
        return redirect(url_for('main.login'))
    
    room = Room.query.get_or_404(room_id)
    
    if action == 'book':
        student = User.query.filter_by(user_id=session['user_id']).first()
        form_data = {
            'student_id': student.user_id if student else '',
            'first_name': student.fname if student else '',
            'last_name': student.lname if student else '',
            'email': student.email if student else '',  
            'action': action,
            'room_id':room_id
        }
        
    if action == 'edit':
        application = Application.query.filter_by(student_id=session['user_id'], room_id=int(room_id)).first()

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
        application = Application.query.filter_by(student_id=session['user_id'], room_id=int(room_id)).first()
        if application:
            errors['room'] = 'You\'ve already booked the selected room'
        
        # Get user entered data 
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
        elif not is_int_like(student_id):
            errors['student_id'] = 'Student ID invalid! Should be an integer.'
        elif  not int(student_id) == session['user_id']:
            errors['student_id'] = 'You cannot book a room using a student ID different from the one you used to log in'
        
        
        if not first_name:
            errors['first_name'] = 'First Name is required.'

        if not last_name:
            errors['last_name'] = 'Last Name is required.'

        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email:  
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

        form_data = {**request.form, 'action': 'book'}
        # If errors exist, return the form with error messages
        if errors:
            room = Room.query.filter_by(id=room_id).first()
            return render_template('book_room.html', errors=errors, room=room, form_data=form_data)

        
        data = Application(
            student_id = student_id,
            first_name = first_name,
            last_name = last_name,
            middle_name = middle_name,
            email = email,
            telephone = telephone,
            gender = gender,
            education_level = education_level,
            program_type = program_type,
            reason_for_applying = reason_for_applying,
            co_curricular_activities = co_curricular_activities,
            agreement = agreement,
            room_id = int(room_id),
            status = "Pending"
        )
        
        db.session.add(data)
        db.session.commit()
        
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    
@main.route('/edit_application/<int:room_id>', methods=['GET', 'POST'])
def edit_application(room_id):
    errors = {}
    
    if session.get('usertype') != 'student':
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.login'))
    
    application = Application.query.filter_by(student_id=session['user_id'], room_id=room_id).first()
    
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

    if not application:
        flash('Application not found.', 'danger')
        return redirect(url_for('main.dashboard.html'))
    # Validation
    if not student_id:
        errors['student_id'] = 'Student ID is required.'
    elif not is_int_like(student_id):
        errors['student_id'] = 'Student ID invalid! Should be an integer.'
    elif  not int(student_id) == session['user_id']:
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
    
    form_data = {**request.form, 'action': 'edit'}

    # If errors exist, return the form with error messages
    if errors:
        room = Room.query.filter_by(id=room_id).first()
        return render_template('book_room.html', errors=errors, room=room, form_data=form_data)

    if request.method == 'POST':
        # Update application attributes with data from the form
        application.first_name = first_name
        application.last_name = last_name
        application.middle_name = middle_name
        application.email = email
        application.telephone = telephone
        application.gender = gender
        application.education_level = education_level
        application.program_type = program_type
        application.reason_for_applying = reason_for_applying
        application.co_curricular_activities = co_curricular_activities
        application.agreement = agreement

        # Save changes to the database
        db.session.commit()
        flash('Application updated successfully.', 'success')
        return redirect(url_for('main.view_booking'))
    
    return render_template('edit_application.html', form_data=form_data, room_id=room_id)

    
@main.route('/view_booking', methods=['GET'])
def view_booking():
    if session.get('usertype') != 'student':
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.dashboard'))
    
    if 'user_id' not in session:
        flash('Please log in to view your bookings', 'danger')
        return redirect(url_for('main.login'))

    student_id = session['user_id']

    bookings = Application.query.filter_by(student_id=student_id).all()
    rooms = [Room.query.get(booking.room_id) for booking in bookings if booking.room_id]

    return render_template('view_booking.html', rooms=rooms)

@main.route('/track_application', methods=['GET', 'POST'])
def track_application():
    statuses = ['Pending', 'Application Approved', 'Payment Under Review', 'Room Booked']

    room_id = request.args.get('room_id')
    student_id = session['user_id']

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
    
    if 'receipt' not in request.files:
        flash(f'No file part', f'danger_{application_id}')
        return redirect(url_for('main.track_application'))

    file = request.files['receipt']
    if file.filename == '':
        flash(f'No selected file', f'danger_{application_id}')
        return redirect(url_for('main.track_application'))

    if file and allowed_file(file.filename):
        # Get the application and its details
        application = Application.query.get(application_id)
        if not application:
            flash(f'Application not found', f'danger_{application_id}')
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
        flash(f'Payment receipt uploaded successfully and is under review.', f'success_{application_id}')
        return redirect(url_for('main.track_application'))
    else:
        flash(f'Invalid file format. Only PDF, JPG, and PNG are allowed.', f'danger_{application_id}')
        return redirect(url_for('main.track_application'))
        # return redirect(url_for('main.track_application', room_id=application_id))
    
    
@main.route('/application_search', methods=['GET', 'POST'])
def application_search():
    
    applications = []
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        room_type = request.form.get('room_type')
        dormitory = request.form.get('dormitory')  
        level = request.form.get('level')  
        
        # Query the database based on the search criteria
        # query = Application.query.join(Room, Application.room_id == Room.id)
        condition = "1 = 1 "
        
        if student_id:
            # query = query.filter_by(student_id=student_id)
            condition += f"and p.student_id = {student_id} "
        if room_type:
            query = query.filter(Room.room_type == room_type)
            condition += f"and r.room_type = {room_type} "
        if dormitory:
            query = query.filter(Room.building == dormitory)
            condition += f"and r.building = {dormitory} "
        if level:
            query = query.filter(Application.education_level == level)
            condition += f"and r.building = {dormitory} "
            
        query = text("""select 
                        p.id AS app_id,
                        p.student_id AS app_student_id,
                        p.first_name AS app_first_name,
                        p.last_name AS app_last_name,
                        p.middle_name AS app_middle_name,
                        p.email AS app_email,
                        p.telephone AS app_telephone,
                        p.gender AS app_gender,
                        p.education_level AS app_education_level,
                        p.program_type AS app_program_type,
                        p.reason_for_applying AS app_reason_for_applying,
                        p.co_curricular_activities AS app_co_curricular_activities,
                        p.agreement AS app_agreement,
                        p.room_id AS app_room_id,
                        p.status AS app_status,
                        r.id AS room_id,
                        r.building AS room_building,
                        r.room_type AS room_room_type,
                        r.floor_number AS room_floor_number,
                        r.description AS room_description,
                        r.total_rooms AS room_total_rooms,
                        r.booked_rooms AS room_booked_rooms,
                        r.available_rooms AS room_available_rooms,
                        r.image_url AS room_image_url
                    FROM applications AS p
                    JOIN rooms AS r ON p.room_id = r.id where """ + condition)
        
        
        
        result = db.session.execute(query)
        applications = result.fetchall()
    
    return render_template('application_search.html', applications=applications)
         


@main.route('/view_application', methods=['GET', 'POST'])
def view_application():
    pass

@main.route('/approve_application/<int:application_id>/<int:room_id>', methods=['GET', 'POST'])
def approve_application(application_id, room_id):
    if session.get('usertype') != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.login'))
    
    application = Application.query.filter_by(id=application_id).first()
    room = Room.query.filter_by(id=room_id).first()
    
    if not application or not room:
        flash("Invalid application or room.", "danger")
        return redirect(url_for('main.dashboard'))
    
    application.status = "Application Approved"
    
    if room.available_rooms <= 0:
        flash('There is no rooms avaiable to book', 'danger')
        return redirect(url_for('main.dashboard')) 
    
    # Save changes to the database
    db.session.commit()
    flash('Application updated successfully.', 'success')
    
    # Send email here
     # Send email notification
    # try:
        # Fetch the email template for "Application Approved"
    template = EmailTemplate.query.filter_by(status="Application Approved").first()
    if not template:
        flash("Email template for 'Application Approved' not found.", "warning")
        return redirect(url_for('main.dashboard'))
    
    approve_user = User.query.filter_by(user_id=session['user_id']).first()
    
    # Replace placeholders in the email body
    email_body = template.body.replace("[Student Name]", f"{application.first_name} {application.last_name}")
    email_body = email_body.replace("[Room Type]", f"{room.room_type}")
    email_body = email_body.replace("[Your Name]", f"{approve_user.fname} {approve_user.lname}")
    
    
    send_email(
    to_email=application.email,
    subject=template.subject,
    content=f'<p>{email_body}</p>'
)
    
    
    return redirect(url_for('main.dashboard'))

@main.route('/view_application_detail', methods=['GET', 'POST'])
def view_application_detail():
    pass

@main.route('/create_email_template', methods=['GET', 'POST'])
def create_email_template():
    templates = EmailTemplate.query.all()
    errors = {}
    if request.method == 'POST':
        
        # Get form data
        status = request.form.get('status')
        subject = request.form.get('subject')
        body = request.form.get('body')

        # Check if template already exists
        template = EmailTemplate.query.filter_by(status=status).first()
        if template:
            errors['status'] = f'Email Template with status {status} already exist!' 
        
        if not subject:
            errors['subject'] = 'Email Subject is required.'
            
        if not body:
            errors['body'] = 'Email Body is required.'
        
        
        if errors:
            return render_template('create_email_template.html', errors=errors, templates=templates, form_data=request.form)

        
        # Create a new template
        new_template = EmailTemplate(status=status, subject=subject, body=body)
        db.session.add(new_template)
        

        # Save changes
        db.session.commit()
        
        # Load existing templates to display
        templates = EmailTemplate.query.all()
    
    return render_template('create_email_template.html', errors=errors, templates=templates)
    
    
    # # Load existing templates to display
    # templates = EmailTemplate.query.all()
    # return render_template('create_email_template.html', templates=templates)



@main.route('/edit_template', methods=['GET', 'POST'])
def edit_template():
    
    template = EmailTemplate.query.filter_by(id=template_id).first()
    form_data = {
        'status': template.status,
        'subject': template.subject,
        'body': template.body
    }
    


@main.route('/system_log', methods=['GET', 'POST'])
def system_log():
    pass

