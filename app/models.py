from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False)
    fname = db.Column(db.String(150), nullable=False)
    lname = db.Column(db.String(150), nullable=False)
    middle_name = db.Column(db.String(100))
    email = db.Column(db.String(150), nullable=False, unique=True)
    telephone = db.Column(db.String(15)) 
    usertype = db.Column(db.String(20), nullable=False) 
    password = db.Column(db.String(150), nullable=False)
    
    
class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    building = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    floor_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    total_rooms = db.Column(db.Integer, nullable=False)
    booked_rooms = db.Column(db.Integer, default=0)
    available_rooms = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)


class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)  
    student_id = db.Column(db.String(20), nullable=False) 
    first_name = db.Column(db.String(100), nullable=False)  
    last_name = db.Column(db.String(100), nullable=False) 
    middle_name = db.Column(db.String(100))  
    email = db.Column(db.String(150), nullable=False)
    telephone = db.Column(db.String(15), nullable=False) 
    gender = db.Column(db.String(10), nullable=False)
    education_level = db.Column(db.String(50), nullable=False) 
    program_type = db.Column(db.String(50), nullable=False) 
    reason_for_applying = db.Column(db.Text, nullable=False)
    co_curricular_activities = db.Column(db.Text)  
    agreement = db.Column(db.Boolean, nullable=False) 
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    status = db.Column(db.String(50))
    
class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), unique=True, nullable=False)  
    subject = db.Column(db.String(200), nullable=False)  
    body = db.Column(db.Text, nullable=False) 