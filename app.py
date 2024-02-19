from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, time, timedelta
import requests
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Password1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

currentUtcTime = datetime.utcnow()
currentDate = currentUtcTime.date()
currentTime = currentUtcTime.time()

# Define relationships

friendslist = db.Table('friendslist',
    db.Column('userId', db.Integer, db.ForeignKey('user.userId'), primary_key = True),
    db.Column('friendId', db.Integer, db.ForeignKey('user.userId'), primary_key = True))

blocklsit = db.Table('blocklist',
    db.Column('userId', db.Integer, db.ForeignKey('user.userId'), primary_key = True),
    db.Column('blockedId', db.Integer, db.ForeignKey('user.userId'), primary_key = True))

user_tags = db.Table('usertags', 
    db.Column('tagId', db.Integer, db.ForeignKey('tags.tagId')),
    db.Column('userId', db.Integer, db.ForeignKey('user.userId'))
)
   
event_tags = db.Table('eventtags',
    db.Column('tagId', db.Integer, db.ForeignKey('tags.tagId')),
    db.Column('eventId', db.Integer, db.ForeignKey('event.eventId'))
)

# define models
class User(db.Model):
    __tablename__ = 'user'
    userId = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), unique=True, nullable=False)
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    dateJoined = db.Column(db.Date, nullable=False)
    birthDate = db.Column(db.Date, nullable=False)
    isOrganiser = db.Column(db.Boolean, nullable=False, default=False)
    interestedTags = db.relationship('Tags', secondary = 'usertags', 
                                backref = db.backref('users'))
    
    friends = db.relationship('User', secondary = friendslist, 
                                primaryjoin = userId == friendslist.c.userId,
                                secondaryjoin = userId == friendslist.c.friendId, 
                                backref = db.backref('friend_of', lazy = 'dynamic'), 
                                lazy = 'dynamic')

    blocked = db.relationship('User', secondary = blocklsit,
                                primaryjoin = userId == blocklsit.c.userId,
                                secondaryjoin = userId == blocklsit.c.blockedId,
                                backref = db.backref('blocked_by', lazy = 'dynamic'),
                                lazy = 'dynamic')
    
    wallPosts = db.relationship('WallPost', backref = 'user', lazy = True)
 
class UserContact(db.Model):
    __tablename__ = 'usercontact'
    contactId = db.Column(db.Integer, primary_key=True)  
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), nullable=False)  
    contactType = db.Column(db.String(50), nullable=False)
    contactValue = db.Column(db.String(50), unique=True, nullable=False)
    contactDescription  = db.Column(db.String(50), nullable=False)

class UserLocation(db.Model):
    __tablename__ = 'userlocation'
    locationID = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

class UserPictures(db.Model):
    __tablename__ = 'userpictures'
    pictureId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), nullable=False)
    picturePath = db.Column(db.String(50), unique=True, nullable=False)
    altText = db.Column(db.String(50), unique=True, nullable=False)
    isProfilePicture = db.Column(db.Boolean, nullable=False, default=False)
    isBannerPicture = db.Column(db.Boolean, nullable=False, default=False)

class UserWall(db.Model):
    __tablename__ = 'userwall'
    wallId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), nullable=False)
    posts = db.relationship('WallPost', backref = 'userwall', lazy = True)

class WallPost(db.Model):
    __tablename__ = 'wallpost'
    postId = db.Column(db.Integer, primary_key=True)
    wallId = db.Column(db.Integer, db.ForeignKey('userwall.wallId'), nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), nullable=False)
    postDate = db.Column(db.Date, nullable=False)
    postTime = db.Column(db.Time, nullable=False)
    postContent = db.Column(db.Text, nullable=False)
    postType = db.Column(db.String(50), nullable=False)
    postVisibility = db.Column(db.String(50), nullable=False)

class Event(db.Model): 
    __tablename__ = 'event'
    eventId = db.Column(db.Integer, primary_key=True)
    organizerId = db.Column(db.Integer, db.ForeignKey('user.userId'), nullable=False)
    eventName = db.Column(db.String(100), unique = True, nullable=False)
    tags = db.relationship('Tags', secondary='eventtags', backref=db.backref('events'))

    organizer = db.relationship('User', backref='events')

class EventDetails(db.Model):
    __tablename__ = 'eventdetails'
    detailId = db.Column(db.Integer, primary_key=True)
    eventId = db.Column(db.Integer, db.ForeignKey('event.eventId'), nullable=False)
    eventDescription = db.Column(db.Text, nullable=False)
    startDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    startTime = db.Column(db.Time, nullable=False)
    endTime = db.Column(db.Time, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
class EventWall(db.Model):
    __tablename__ = 'eventwall'
    eventWallId = db.Column(db.Integer, primary_key=True)
    eventId = db.Column(db.Integer, db.ForeignKey('event.eventId'), nullable=False)

class Tags(db.Model):
    __tablename__ = 'tags'
    tagId = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(50), unique=True, nullable=False)

def openStreetMapGeocode(address):
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json"
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    # Parse the response and extract coordinates
    if data:
        latitude = data[0]['lat']
        longitude = data[0]['lon']
        return latitude, longitude
    else:
        return None, None
    
def openStreetMapReverseGeocode(latitude, longitude):
    base_url = "https://nominatim.openstreetmap.org/reverse"  
    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "json"
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    # Parse the response and extract address
    if 'display_name' in data:
        address = data['display_name']
        return address
    else:
        return None
    
def mapBoxgeocode(address):
    baseUrl = "https://api.mapbox.com/geocoding/v5/mapbox.places/"
    accessToken = "pk.eyJ1IjoidGlta2MiLCJhIjoiY2xzc3czcTg2MGdtbzJqcGdxdmxkdGI0NiJ9.ZamkOoED2_ug0q_Meb7drw"
    endpoint = f"{address}.json"

    params = {
        "access_token": accessToken,
        "limit": 1
    }

    response = requests.get(baseUrl + endpoint, params=params)
    data = response.json()

    if data.get('features'):
        #Extract latitude and longitude from the first result
        latitude = data['features'][0]['center'][1]
        longitude = data['features'][0]['center'][0]
        placeName = data['features'][0]['place_name']
        return latitude, longitude, placeName
    else:
        return None, None
    
def mapBoxReverseGeocode(latitude, longitude):
    baseUrl = "https://api.mapbox.com/geocoding/v5/mapbox.places/"
    accessToken = "pk.eyJ1IjoidGlta2MiLCJhIjoiY2xzc3czcTg2MGdtbzJqcGdxdmxkdGI0NiJ9.ZamkOoED2_ug0q_Meb7drw"
    endpoint = f"{longitude},{latitude}.json"

    params = {
        "access_token": accessToken,
        "limit": 1
    }

    response = requests.get(baseUrl + endpoint, params=params)
    data = response.json()

    if data.get('features'):
        #Extract address from the first result
        address = data['features'][0]['place_name']
        return address
    else:
        return None
    
def geocode(address):
    baseUrl = "https://maps.googleapis.com/maps/api/geocode/json"
    apiKey = "AIzaSyAknTozLR6kcm24rkpgc8kdykbUv8hSTeU"

    params = {
        "address": address,
        "key": apiKey
    }

    response = requests.get(baseUrl, params = params)
    data = response.json()

    if data.get('results'):
        #Extract latitude and longitude from the first result
        latitude = data['results'][0]['geometry']['location']['lat']
        longitude = data['results'][0]['geometry']['location']['lng']
        return latitude, longitude
    else:
        return None, None
    
def reverseGeocode(latitude, longitude):
    baseUrl = "https://maps.googleapis.com/maps/api/geocode/json"
    apiKey = "AIzaSyAknTozLR6kcm24rkpgc8kdykbUv8hSTeU"

    params = {
        "latlng": f"{latitude},{longitude}",
        "key": apiKey
    }

    response = requests.get(baseUrl, params = params)
    data = response.json()

    if data.get('results'):
        for result in data['results']:
        # Check if result_type is street_address
            if 'street_address' in result['types']:
                return result['formatted_address']
            # If street address not found, check for postal_code
            elif 'postal_code' in result['types']:
                address = result['formatted_address']
        return address
    else:
        return None

# Routes
@app.route('/')
def home(): 
    latest_events = Event.query.order_by(Event.eventId.desc()).limit(3).all()
    latest_descriptions = EventDetails.query.order_by(EventDetails.detailId.desc()).limit(3).all()
    
    # Perform reverse geocoding for each event
    for event in latest_descriptions:
        latitude = event.latitude
        longitude = event.longitude
        address = reverseGeocode(latitude, longitude)
        event.address = address
    
    return render_template('home.html', latest_events=latest_events, latest_descriptions=latest_descriptions)

# Update Location
@app.route('/update_location', methods=['GET', 'POST'])
def update_location():
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401
    
    # Get latitude and longitude data from the request
    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    # Update latitude and longitude for the user in the database
    user_id = session['user_id']
    user = User.query.get(user_id)
    if user:
        UserLocation.latitude = latitude
        UserLocation.longitude = longitude
        db.session.commit()
        return jsonify({'message': 'Location updated successfully'}), 200
    else:
        return jsonify({'error': 'User not found'}), 404

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        birthdate = request.form['birthdate']
        isOrganiser = request.form.get('isOrganiser')

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username is already taken. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        
        #Check if password and confirm_password match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))

        # Check if email already exists
        existing_email = UserContact.query.filter_by(contactValue=email).first()
        if existing_email:
            flash('Email address is already registered. Please use a different email.', 'danger')
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        cleansedDate = datetime.strptime(birthdate, '%Y-%m-%d').date()
        isOrg = request.form.get('isOrganiser') == 'on'

        # Create the new user
        user = User(username=username, firstName = firstname, lastName = lastname, dateJoined = currentDate, birthDate = cleansedDate, isOrganiser = isOrg)
        db.session.add(user)
        db.session.commit()

        userId = user.userId

        # Create a new user auth record
        user_auth = User(userId = userId, password = hashed_password)
        db.session.add(user_auth)
        db.session.commit()

        # Create a new user contact record
        userContact = UserContact(userId = userId, contactType = 'email', contactValue = email, contactDescription = 'Primary email')
        db.session.add(userContact)
        db.session.commit()

        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            # If the user exists, query the User table for the corresponding password
            userAuth = User.query.filter_by(userId=user.userId).first()
            if userAuth and bcrypt.check_password_hash(userAuth.password, password):
                session['user_id'] = user.userId
                flash('Logged in successfully', 'success')
                return redirect(url_for('home'))
            else:
                flash('Login failed. Please check your credentials.', 'danger')
    return render_template('login.html')

# User Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

# Create Event (Requires login)
@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'user_id' not in session:
        flash('Please log in to create an event.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        organizerId = session['user_id']
        latitude, longitude = get_location()
        if latitude is not None and longitude is not None:
            event = Event(name=name, description=description, organizerId=organizerId,
                          location=f"(latitude, longitude)")

            db.session.add(event)
            db.session.commit()
            flash('Event created successfully', 'success')
            return redirect(url_for('home'))
        else:
            flash('Failed to get your location. Please try again.', 'danger')
    return render_template('create_event.html')

def create_sample_data():
    
    # Clear existing data
    User.query.delete()
    UserContact.query.delete()
    UserLocation.query.delete()
    UserPictures.query.delete()
    UserWall.query.delete()
    WallPost.query.delete()
    Event.query.delete()
    EventDetails.query.delete()
    EventWall.query.delete()
    Tags.query.delete()
    db.session.commit()

    password1 = 'password1'
    hashedPassword1 = bcrypt.generate_password_hash(password1).decode('utf-8')
    password2 = 'password2'
    hashedPassword2 = bcrypt.generate_password_hash(password2).decode('utf-8')

    user1 = User(username = 'user1', password = hashedPassword1, firstName = 'First1', lastName = 'Last1', dateJoined = currentDate, birthDate = currentDate, isOrganiser = False)
    user2 = User(username = 'user2', password = hashedPassword2, firstName = 'First2', lastName = 'Last2', dateJoined = currentDate, birthDate = currentDate, isOrganiser = False)

    # Add sample users to the database
    db.session.add(user1)
    db.session.add(user2)

    userContact1 = UserContact(userId = 1, contactType = 'email', contactValue = 'user1@email.com', contactDescription = 'Primary email')
    userContact2 = UserContact(userId = 2, contactType = 'email', contactValue = 'user2@email.com', contactDescription = 'Primary email')

    db.session.add(userContact1)
    db.session.add(userContact2)

    # Create sample data
    event1 = Event(organizerId = 2, eventName='Event 1')
    event2 = Event(organizerId = 2, eventName='Event 2')

    # Add sample events to the database
    db.session.add(event1)
    db.session.add(event2)

    eventdetails1 = EventDetails(eventId = 1, eventDescription = 'a random test for the database', startDate = currentDate, endDate = currentDate + timedelta(days = 2), startTime = currentTime, endTime = currentTime, latitude = 52.0588862, longitude = -1.0317558)
    eventdetails2 = EventDetails(eventId = 2, eventDescription = 'a second test for the database', startDate = currentDate, endDate = currentDate + timedelta(days = 2), startTime = currentTime, endTime = currentTime, latitude = 51.50292959999999, longitude = -2.5525405)
    db.session.add(eventdetails1)
    db.session.add(eventdetails2)

    # Commit changes to the database
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='user1').first() or not Event.query.filter_by(eventName='event1').first():
            create_sample_data()
    app.run(debug=True)