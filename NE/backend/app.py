import datetime
import xml.etree.ElementTree as ET 
import re 
import html 
from flask import Flask, request, jsonify, Response,send_from_directory
from flask_cors import CORS
from flask_mail import Mail, Message
from bson import ObjectId
from pymongo import MongoClient
import bcrypt 
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import PyPDF2
from docx import Document
import csv 
import io
import os
import math
import re 
import numpy as np  
import random
import csv
import io
from lxml import etree 
import secrets
import string
from werkzeug.utils import secure_filename
import traceback 
import jwt
from functools import wraps
from flask import request, jsonify


# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'  
app.config['JWT_ALGORITHM'] = 'HS256' 
app.config['JWT_EXPIRATION_HOURS'] = 24  

# --- MongoDB Connection ---
client = MongoClient("mongodb://localhost:27017/")
db = client["NER_Tool"]

# --- Mail Configuration ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'mwa.iiith@gmail.com'
app.config['MAIL_PASSWORD'] = 'jjmd umfd lpds yzvh'      
mail = Mail(app)

# --- Collections (Updated) ---
users_collection = db["users"]
sentences_collection = db["sentences"]
user_activities_collection = db["user_activities"]
user_session_history_collection = db["user_session_history"]
tags_collection = db["tags"]             # FINAL/APPROVED tags
projects_collection = db["projects"]
search_tags_collection = db["search_tags"] 
feedback_collection = db["feedback"] 
org_admins_collection = db["org_admins"]
staged_tags_collection = db["staged_tags"]
revision_notes_collection = db["revision_notes"] 
# --- Helper Functions (UNCHANGED) ---



# --- Configuration (UNCHANGED) ---
UPLOAD_FOLDER = 'feedback_uploads'
# Set maximum upload size to 5 megabytes
MAX_CONTENT_LENGTH = 5 * 1024 * 1024 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
PORT = 5001



app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to check file extension (UNCHANGED)
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_ist_time():
    """Get current IST time"""
    IST = ZoneInfo("Asia/Kolkata")
    return datetime.now(IST)

# --- JWT Helper Functions ---

def generate_jwt_token(username, role):
    """Generate JWT token for authenticated user"""
    try:
        IST = ZoneInfo("Asia/Kolkata")
        payload = {
            'username': username,
            'role': role,
            'exp': datetime.now(IST) + timedelta(hours=app.config['JWT_EXPIRATION_HOURS']),  # CHANGE HERE
            'iat': datetime.now(IST)  # CHANGE HERE
        }   
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm=app.config['JWT_ALGORITHM'])
        return token
    except Exception as e:
        print(f"Error generating JWT token: {e}")
        return None

def verify_jwt_token(token):
    """Verify JWT token and return payload if valid"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=[app.config['JWT_ALGORITHM']])
        
        # Additional check: verify user still exists and has same role
        user = users_collection.find_one({"username": payload.get('username')})
        if not user:
            return None  # User no longer exists
            
        # Optional: Verify role hasn't changed
        if user.get('role') != payload.get('role'):
            # Role changed, token is outdated
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

def token_required(f):
    """Decorator to protect routes that require JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        
        # Verify token
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({"message": "Token is invalid or expired"}), 401
        
        # Add user info to request context for use in the route
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to protect routes that require admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        
        # Verify token
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({"message": "Token is invalid or expired"}), 401
        
        # Check if user is admin
        if payload.get('role') != 'admin':
            return jsonify({"message": "Admin access required"}), 403
        
        # Add user info to request context for use in the route
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated


def developer_required(f):
    """Decorator to protect routes that require developer role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header (same as admin_required)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        
        # Verify token (same as admin_required)
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({"message": "Token is invalid or expired"}), 401
        
        # Check if user is developer (THE CRITICAL DIFFERENCE)
        if payload.get('role') != 'developer':
            return jsonify({"message": "Developer access required"}), 403
        
        # Add user info to request context for use in the route
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated

@app.route('/feedback_uploads/<filename>')
def serve_feedback_image(filename):
    """Serve uploaded feedback images (UNCHANGED)"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    
def send_org_admin_notification(new_user_data):
    """Sends an email to the organization administrator about a new user pending approval. (UNCHANGED)"""
    
    # Find organization admin(s)
    org_admins = org_admins_collection.find({"organization": new_user_data['organization']})
    
    admin_emails = [admin['email'] for admin in org_admins]
    
    if not admin_emails:
        print(f"No admin found for organization: {new_user_data['organization']}")
        return
    
    try:
        msg = Message(
            subject=f"ACTION REQUIRED: New User Registration - {new_user_data['full_name']}",
            sender=app.config['MAIL_USERNAME'],
            recipients=admin_emails
        )
        
        msg.body = f"""
Dear Administrator,

A new user has registered and is awaiting your approval:

User Details:
- Full Name: {new_user_data['full_name']}
- Email: {new_user_data['email']}
- Organization: {new_user_data['organization']}
- Role: {new_user_data['role']}
- Languages: {', '.join(new_user_data['languages']) if new_user_data['languages'] else 'N/A'}
- Registration Date: {get_ist_time().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please log in to the admin panel to review and approve/reject this registration.

Best regards,
Sentence Annotation System
"""
        mail.send(msg)
        print(f"Notification sent to org admin(s): {admin_emails}")
        
    except Exception as e:
        print(f"Failed to send org admin notification: {e}")

def send_user_approval_email(user_data, approved=True):
    """Sends approval or rejection email to the user. (UNCHANGED)"""
    
    try:
        if approved:
            subject = "Account Approved - Sentence Annotation System"
            body = f"""
Dear {user_data['full_name']},

Your account registration has been approved by the administrator.

You can now log in to the Sentence Annotation System using your credentials:
- Username: {user_data['email']}

Access the system at: [Your System URL]

If you have any questions, please contact your organization administrator.

Best regards,
Sentence Annotation System Team
"""
        else:
            subject = "Account Registration Rejected"
            body = f"""
Dear {user_data['full_name']},

We regret to inform you that your account registration has been rejected by the administrator.

Organization: {user_data.get('organization', 'N/A')}

If you believe this is an error, please contact your organization administrator.

Best regards,
Sentence Annotation System Team
"""
        
        msg = Message(
            subject=subject,
            sender=app.config['MAIL_USERNAME'],
            recipients=[user_data['email']]
        )
        msg.body = body
        mail.send(msg)
        print(f"{'Approval' if approved else 'Rejection'} email sent to: {user_data['email']}")
        
    except Exception as e:
        print(f"Failed to send user {'approval' if approved else 'rejection'} email: {e}")


def send_admin_welcome_email(user_data):
    """Sends welcome email to newly registered admin users. (UNCHANGED)"""
    try:
        msg = Message(
            subject="Welcome to Sentence Annotation System - Admin Account Activated",
            sender=app.config['MAIL_USERNAME'],
            recipients=[user_data['email']]
        )
        
        msg.body = f"""
Dear {user_data['full_name']},

Your administrator account has been successfully created and activated.

You can now log in to the Sentence Annotation System using your credentials:
- Username: {user_data['email']}

As an administrator, you have access to:
- User management and approval
- Project creation and assignment
- System monitoring and reports

Access the system at: [Your System URL]

Best regards,
Sentence Annotation System Team
"""
        mail.send(msg)
        print(f"Welcome email sent to new admin: {user_data['email']}")
        
    except Exception as e:
        print(f"Failed to send admin welcome email: {e}")
        
def update_session_history_report(username_to_update):
    """Recalculates and saves the session history for a specific user with proper logout handling"""
    logs_list = []
    UTC = ZoneInfo("UTC")
    IST = ZoneInfo("Asia/Kolkata")
    
    user_activity_doc = user_activities_collection.find_one({'username': username_to_update})
    if not user_activity_doc or not user_activity_doc.get('activities'): 
        return

    activities = sorted(user_activity_doc.get('activities', []), key=lambda x: x['timestamp'])
    session = None
    
    for act in activities:
        desc = act['description']
        utc_ts = act['timestamp']
        
        if desc == "Login":
            # Close previous session if exists
            if session:
                # Only add session if it has real tasks OR was properly closed
                if session["tasksDone"] or session["logoutTimeIST"]:
                    logs_list.append(session)
                # Otherwise, discard empty active sessions that were never properly closed
                elif not session["logoutTimeIST"]:
                    print(f"DEBUG: Discarding unclosed session for {username_to_update} at login")
            
            login_ist = utc_ts.replace(tzinfo=UTC).astimezone(IST)
            session = {
                "id": f"{username_to_update}_{utc_ts.timestamp()}",
                "username": username_to_update,
                "loginTimeIST": login_ist.strftime('%d/%m/%Y, %H:%M:%S'),
                "logoutTimeIST": None, 
                "tasksDone": []
            }
            
        elif desc == "Logout" and session:
            logout_ist = utc_ts.replace(tzinfo=UTC).astimezone(IST)
            session["logoutTimeIST"] = logout_ist.strftime('%d/%m/%Y, %H:%M:%S')
            
            # Always add session when logout is recorded, even if no tasks
            logs_list.append(session)
            session = None  # Clear the session after logout
            
        elif session and desc not in ["Login", "Logout"]:
            # Add real task to current session, avoiding duplicates
            if desc not in session["tasksDone"]:
                session["tasksDone"].append(desc)
    
    # Handle the last session if it wasn't closed (active session)
    if session and not session["logoutTimeIST"]:
        # Check if this session has any real activities
        hasRealActivities = any(task not in ["Session ended with no tasks", "Active session - no tasks recorded"] 
                              for task in session["tasksDone"])
        
        if hasRealActivities:
            # Only keep active sessions that have real activities
            logs_list.append(session)
            print(f"DEBUG: Keeping active session for {username_to_update} with real activities")
        else:
            print(f"DEBUG: Discarding inactive session for {username_to_update} with no real activities")

    # Sort sessions by login time (newest first)
    sorted_sessions = sorted(logs_list, key=lambda s: datetime.strptime(s.get('loginTimeIST', '01/01/1970, 00:00:00'), '%d/%m/%Y, %H:%M:%S'), reverse=True)
    
    # Update the session history
    user_session_history_collection.update_one(
        {'username': username_to_update},
        {'$set': {'sessions': sorted_sessions}},
        upsert=True
    )
    print(f"User session history for '{username_to_update}' has been updated with {len(sorted_sessions)} sessions.")

def log_action_and_update_report(username, description):
    """Logs a new raw event and triggers a rebuild of that user's session history report. (UNCHANGED)"""
    user_activities_collection.update_one(
        {'username': username},
        {'$push': {'activities': {"timestamp": get_ist_time(), "description": description}}},
        upsert=True
    )
    update_session_history_report(username)

def clean_sentence_text(text):
    """
    Removes common leading numbering patterns (1., 1.1., A., etc.) and excessive whitespace. (UNCHANGED)
    """
    if not text:
        return ""
    
    text = re.sub(r'^\s*(\d+(\.\d+)*[\.\)\s]+\s*|[a-zA-Z][\.\)\s]+\s*)', '', text).strip()
    
    return text.strip()


def extract_from_xml(file):
    """
    Parses sentences and annotations directly from the structured XML file format.
    Returns a list of dictionaries containing sentence text, status, and tags.
    """
    sentences_data = []
    
    file.seek(0)
    xml_content = file.read()
    if not xml_content:
        return sentences_data

    try:
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(xml_content, parser=parser)
        
        print(f"DEBUG: Root tag: {root.tag}")
        
        # Check if this is the project > sentences > sentence structure
        sentences_root = root.find(".//sentences")
        if sentences_root is not None:
            print("DEBUG: Found sentences root element")
            sentence_elems = sentences_root.findall(".//sentence")
        else:
            # Fallback: look for sentence elements anywhere
            sentence_elems = root.findall(".//sentence")
        
        print(f"DEBUG: Found {len(sentence_elems)} sentence elements")
        
        for sentence_elem in sentence_elems:
            # Get text from 'text' attribute
            text_content = sentence_elem.get('text', '').strip()
            
            # Get is_annotated from attribute
            is_annotated_attr = sentence_elem.get('isAnnotated', '').strip().lower()
            if is_annotated_attr:
                is_annotated = is_annotated_attr == 'true'
            else:
                # Fallback to old format
                is_annotated_text = sentence_elem.findtext('is_annotated', default='False').strip()
                is_annotated = is_annotated_text.lower() == 'true'
            
            tags = []
            annotations_elem = sentence_elem.find('annotations')
            if annotations_elem is not None:
                annotation_elems = annotations_elem.findall('annotation')
                print(f"DEBUG: Found {len(annotation_elems)} annotation elements for sentence: {text_content[:50]}...")
                
                for annotation_elem in annotation_elems:
                    # Get annotation data from attributes
                    word_phrase = annotation_elem.get('word_phrase', '').strip()
                    annotation_type = annotation_elem.get('annotation', '').strip()
                    annotated_by = annotation_elem.get('annotated_by', '').strip()
                    annotated_on = annotation_elem.get('annotated_on', '').strip()
                    
                    print(f"DEBUG: Annotation found - word_phrase: '{word_phrase}', type: '{annotation_type}', by: '{annotated_by}', on: '{annotated_on}'")
                    
                    if word_phrase and annotation_type:
                        tags.append({
                            'tag': annotation_type,
                            'text': word_phrase,
                            'annotated_by': annotated_by,
                            'annotated_on': annotated_on
                        })
            
            if text_content:
                sentences_data.append({
                    "textContent": text_content,
                    "is_annotated": is_annotated,
                    "tags": tags 
                })
                print(f"DEBUG: Added sentence: '{text_content}' with {len(tags)} tags, is_annotated: {is_annotated}")
                
    except etree.XMLSyntaxError as e:
        print(f"XML Parsing Error: {e}")
        raise ValueError("Invalid XML file structure.")
    except Exception as e:
        print(f"Generic XML Extraction Error: {e}")
        print(f"Error details: {traceback.format_exc()}")
        raise ValueError("Failed to process XML content.")

    print(f"DEBUG: Total sentences extracted: {len(sentences_data)}")
    return sentences_data

def extract_text_from_file(file, file_extension):
    """
    Extracts text and annotation metadata from uploaded files for project creation. (UNCHANGED)
    """
    if file_extension == '.xml':
        return extract_from_xml(file)

    sentences_data = []
    
    # Regex patterns for structured annotation format
    SENTENCE_LINE_REGEX = re.compile(r"^Sentence ID:\s*\d+,\s*Text:\s*'([^']*)'")
    ANNOTATION_LINE_REGEX = re.compile(
        r'^\s*Annotation:\s*(?P<tag>[^,]+),\s*Word_Phrase:\s*\'(?P<text>.*?)\',\s*Annotated by:\s*(?P<by>[^,]+),\s*Annotated on:\s*(?P<on>[^\s]+)'
    )
    
    try:
        file.seek(0)
        raw_text = ""
        
        # Read file content based on file type
        if file_extension == '.txt':
            raw_text = file.read().decode('utf-8', errors='ignore')
        elif file_extension == '.pdf':
            # PDF text extraction
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                raw_text += page.extract_text() + "\n"
        elif file_extension in ['.doc', '.docx']:
            # DOCX text extraction
            doc = Document(file)
            for paragraph in doc.paragraphs:
                raw_text += paragraph.text + "\n"
        elif file_extension == '.csv':
            # CSV text extraction - read all cells
            csv_content = file.read().decode('utf-8', errors='ignore')
            csv_reader = csv.reader(io.StringIO(csv_content))
            for row in csv_reader:
                for cell in row:
                    if cell.strip():
                        raw_text += cell.strip() + " "
                raw_text += "\n"
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Check if this is a structured file (with Sentence ID patterns) or plain text
        if SENTENCE_LINE_REGEX.search(raw_text):
            # Process as structured file with annotations
            print("Detected structured annotation file format")
            raw_lines = raw_text.split('\n')
            current_sentence = None
            
            for line in raw_lines:
                line = line.strip()
                if not line:
                    continue

                # Check for Sentence line
                sentence_match = SENTENCE_LINE_REGEX.match(line)
                if sentence_match:
                    # If we have a previous sentence, add it to the list
                    if current_sentence:
                        sentences_data.append(current_sentence)
                    
                    # Start new sentence
                    text_content = sentence_match.group(1).strip()
                    if text_content:
                        current_sentence = {
                            "textContent": text_content,
                            "is_annotated": False,
                            "tags": []
                        }
                    continue

                # Check for Annotation line
                annotation_match = ANNOTATION_LINE_REGEX.match(line)
                if annotation_match and current_sentence:
                    # Mark the current sentence as annotated
                    current_sentence['is_annotated'] = True
                    
                    # Extract annotation data
                    tag_data = annotation_match.groupdict()
                    tag_record = {
                        'tag': tag_data['tag'].strip(),
                        'text': tag_data['text'].strip(),
                        'annotated_by': tag_data['by'].strip(),
                        'annotated_on': tag_data['on'].strip(),
                    }
                    current_sentence['tags'].append(tag_record)
                    continue

            # Don't forget to add the last sentence
            if current_sentence:
                sentences_data.append(current_sentence)
                
        else:
            # Process as plain text with Hindi/English punctuation
            print("Detected plain text format - splitting by punctuation")
            
            # Enhanced sentence splitting for multiple languages
            # Split on Hindi full stop (।), double danda (॥), and standard punctuation
            sentences = re.split(r'([।|॥|\.|\?|!]+)\s*', raw_text)
            
            # Reconstruct sentences with their punctuation
            reconstructed_sentences = []
            i = 0
            while i < len(sentences):
                sentence_text = sentences[i].strip()
                if i + 1 < len(sentences) and sentences[i + 1].strip() in ['।', '॥', '.', '?', '!']:
                    # Add punctuation back to the sentence
                    sentence_text += sentences[i + 1].strip()
                    i += 2
                else:
                    i += 1
                
                if sentence_text:
                    reconstructed_sentences.append(sentence_text)
            
            # If the above method doesn't work well, fall back to simple splitting
            if not reconstructed_sentences:
                sentences = re.split(r'[।|॥|\.|\?|!]\s*', raw_text)
                reconstructed_sentences = [s.strip() + '.' for s in sentences if s.strip()]
            
            # Clean and add sentences
            for sentence_text in reconstructed_sentences:
                clean_text = sentence_text.strip()
                if clean_text and len(clean_text) > 1:  # Filter out very short strings
                    # Remove excessive whitespace
                    clean_text = re.sub(r'\s+', ' ', clean_text)
                    
                    sentences_data.append({
                        "textContent": clean_text,
                        "is_annotated": False,
                        "tags": []
                    })
            
            print(f"Extracted {len(sentences_data)} sentences from plain text")
            
    except PyPDF2.PdfReadError as e:
        raise ValueError(f"Invalid PDF file: {str(e)}")
    except Exception as e:
        print(f"Error parsing file {file_extension}: {e}")
        raise ValueError(f"Failed to parse file: {str(e)}")
        
    return sentences_data


def log_reviewer_action(reviewer_username, action_description, annotator_username=None):
    """Enhanced logging for reviewer actions"""
    # Log for reviewer
    log_action_and_update_report(reviewer_username, action_description)
    
    # Also log for annotator if provided
    if annotator_username and annotator_username != reviewer_username:
        user_action = action_description.replace("reviewed", "had work reviewed")
        log_action_and_update_report(annotator_username, user_action)



def update_sentence_review_status(sentence_id):
    """Update sentence review status based on its tags with enhanced mixed-status handling"""
    try:
        from bson.objectid import ObjectId
        
        # Count remaining staged tags for this sentence
        remaining_staged_tags = staged_tags_collection.count_documents({
            "source_sentence_id": sentence_id,
            "review_status": "Pending"  # Only count pending ones
        })
        
        # Count approved tags for this sentence
        approved_tags_count = tags_collection.count_documents({
            "source_sentence_id": sentence_id
        })
        
        # Count rejected tags for this sentence
        rejected_tags_count = staged_tags_collection.count_documents({
            "source_sentence_id": sentence_id,
            "review_status": "Rejected"
        })
        
        # Get current sentence
        sentence = sentences_collection.find_one({"_id": ObjectId(sentence_id)})
        if not sentence:
            return
            
        current_status = sentence.get('review_status', 'Pending')
        annotator_username = sentence.get('username')
        
        # Determine is_annotated based on the existence of any tags
        is_annotated = (remaining_staged_tags > 0) or (approved_tags_count > 0) or (rejected_tags_count > 0) or sentence.get('is_annotated', False)
        
        # ENHANCED: Determine the correct status for mixed scenarios
        if remaining_staged_tags > 0:
            # Some tags still pending review
            new_status = "Pending"
        elif approved_tags_count > 0 and rejected_tags_count == 0:
            # All tags approved, none rejected
            new_status = "Approved"
        elif approved_tags_count == 0 and rejected_tags_count > 0:
            # All tags rejected, none approved
            new_status = "Rejected"
        elif approved_tags_count > 0 and rejected_tags_count > 0:
            # MIXED STATUS: Some approved, some rejected
            new_status = "Partially Approved"
        else:
            # No tags at all
            if is_annotated:
                new_status = "Rejected"
            else:
                new_status = "Pending"

        # Update the sentence
        sentences_collection.update_one(
            {"_id": ObjectId(sentence_id)},
            {"$set": {
                "review_status": new_status,
                "is_annotated": is_annotated
            }}
        )
        
        # Log status change
        if current_status != new_status and annotator_username:
            status_change_msg = f"Sentence status changed from '{current_status}' to '{new_status}'"
            log_action_and_update_report(annotator_username, status_change_msg)
        
        print(f"Updated sentence {sentence_id} status: {new_status} (approved: {approved_tags_count}, rejected: {rejected_tags_count}, pending: {remaining_staged_tags})")
        
    except Exception as e:
        print(f"Error updating sentence status: {e}")
        
# --- API Routes ---

@app.route("/api/log-action", methods=["POST"])
@token_required
def log_user_action():
    """Endpoint for logging user actions from the frontend"""
    try:
        data = request.json
        username = data.get("username")
        description = data.get("description")
        
        if not username or not description:
            return jsonify({"error": "Username and description are required"}), 400
            
        log_action_and_update_report(username, description)
        return jsonify({"message": "Action logged successfully"}), 200
        
    except Exception as e:
        print(f"Error logging action: {e}")
        return jsonify({"error": "Internal server error"}), 500
    

def send_developer_notification(new_user_data, approval_target):
    """Sends an email to a system owner or existing developer about a pending Admin/Developer registration."""
    
    # 1. Find existing Approved Developer email(s) for notification
    # This ensures only currently approved developers get the approval request.
    developer_emails = [
        user['email'] for user in users_collection.find({"role": "developer", "is_approved": True})
    ]
    
    # Fallback/Default Recipient if no approved developers exist (e.g., system owner)
    if not developer_emails:
        print("ALERT: No approved developers found. Sending notification to default system email.")
        developer_emails.append(app.config['MAIL_USERNAME']) # Sends to the mail sender address

    try:
        msg = Message(
            subject=f"ACTION REQUIRED: New {new_user_data['role'].upper()} Registration - {new_user_data['full_name']}",
            sender=app.config['MAIL_USERNAME'],
            recipients=developer_emails
        )
        
        msg.body = f"""
Dear System Owner/Developer,

A new user with the role '{new_user_data['role'].upper()}' has registered and requires your approval:

User Details:
- Role: {new_user_data['role'].upper()}
- Full Name: {new_user_data['full_name']}
- Email: {new_user_data['email']}
- Organization: {new_user_data['organization']}
- Registration Date: {get_ist_time().strftime('%Y-%m-%d %H:%M:%S IST')}

This user cannot log in until you approve their account via the Developer Dashboard.

Best regards,
Sentence Annotation System
"""
        mail.send(msg)
        print(f"Developer notification sent to: {developer_emails}")
        
    except Exception as e:
        print(f"Failed to send developer notification: {e}")
        # Log the detailed exception for debugging
        import traceback
        traceback.print_exc()

def send_org_admin_notification(user_data):
    """Placeholder to notify Org Admins about a pending Annotator/Reviewer registration."""
    print(f"NOTIFICATION: New {user_data.get('role')} registered ({user_data.get('email')}). Requires Org Admin approval.")
    # Add actual email/notification logic here

def send_developer_welcome_email(user_data):
    """Sends a welcome email to a newly auto-approved developer user."""
    try:
        msg = Message(
            subject="Welcome to System - Developer Account Activated",
            sender=app.config['MAIL_USERNAME'],
            recipients=[user_data['email']]
        )
        
        msg.body = f"""
Dear {user_data['full_name']},

Your Developer account has been automatically approved and activated.

You can now log in to the system immediately using your credentials. As a Developer, you have system-level access to management and reporting tools.

Access the system at: [Your System URL]

Best regards,
System Team
"""
        mail.send(msg)
        print(f"Welcome email sent to new developer: {user_data['email']}")
        
    except Exception as e:
        print(f"Failed to send developer welcome email: {e}")

def log_action_and_update_report(actor, message):
    """Placeholder for logging system activities."""
    print(f"LOG: [{actor}] {message}")



    
@app.route("/register", methods=["POST"])
def register():
    """Handles user registration with IST timestamps."""
    data = request.json
    username, password, email, role = data.get("email"), data.get("password"), data.get("email"), data.get("role")
    
    full_name = data.get("fullName", "N/A")
    organization = data.get("organization", "N/A")
    languages = data.get("languages", [])

    if not all([username, password, email, role]): 
        return jsonify({"message": "All required fields are mandatory"}), 400
    
    is_developer = role.lower() == "developer"
    
    # Conditional Field Validation (Organization is required for non-developers)
    if not is_developer and organization in ["N/A", "", None]:
         return jsonify({"message": "Organization is mandatory for non-developer roles"}), 400
         
    if users_collection.find_one({"username": username}): 
        return jsonify({"message": "Account with this email already exists"}), 400

    # --- NEW Developer Logic: Check Limit and Auto-Approve ---
    
    # 1. Developer Limit Check
    if is_developer: 
        developer_count = users_collection.count_documents({"role": "developer"})
        if developer_count >= 2:
            return jsonify({"message": "Maximum limit of 2 developers has been reached. Developer registration failed."}), 403
            
        # 2. Auto-Approval for Developer role (up to the limit)
        is_approved = True
        organization = "SYSTEM_DEVELOPER" # Enforce default for consistency
        languages = ["N/A"] 
    else:
        # 3. All other roles (Admin, User, Reviewer) REQUIRE approval
        is_approved = False
    
    # --- End NEW Developer Logic ---
    
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    
    # Use IST timezone
    IST = ZoneInfo("Asia/Kolkata")
    registration_time_ist = datetime.now(IST)
    
    # Insert new user record
    user_data = {
        "username": username, 
        "full_name": full_name, 
        "email": email, 
        "password": hashed_pw, 
        "role": role, 
        "organization": organization,
        "languages": languages, 
        "is_approved": is_approved, # NOW TRUE FOR DEVELOPER
        "registered_at": registration_time_ist,
        # Auto-set approval fields if auto-approved
        "approved_by": "system_auto" if is_approved else None, 
        "approved_at": registration_time_ist if is_approved else None, 
        "rejection_reason": None
    }
    
    users_collection.insert_one(user_data)
    
    # ... (user activities and session history inserts remain here) ...
    
    # Collect data for the email notification
    user_data_for_email = {
        "full_name": full_name, 
        "email": email, 
        "role": role, 
        "organization": organization,
        "languages": languages
    }
    
    # --- NEW Post-Registration Flow ---
    
    if role.lower() == "developer":
        # Auto-approved developer - send welcome email (now defined below)
        send_developer_welcome_email(user_data_for_email)
        log_action_and_update_report("system", f'New DEVELOPER user registered and auto-approved: {username}.')
        return jsonify({"message": "Developer registered successfully. You can login immediately."})
        
    elif role.lower() == "admin":
        # Admins need to be approved by a Developer (Notification remains the same)
        send_developer_notification(user_data_for_email, approval_target="Developer")
        log_action_and_update_report("system", f'New ADMIN user registered: {username}. Awaiting approval by Developer.')
        return jsonify({"message": "Admin registered successfully. Awaiting developer approval."})

    else: # Regular user (Annotator OR Reviewer) - Awaiting Admin approval
        send_org_admin_notification(user_data_for_email)
        log_action_and_update_report("system", f'New user registered: {username}. Awaiting Organization Admin approval.')
        return jsonify({"message": "User registered successfully. Awaiting admin approval."})
    
@app.route("/api/org-admins", methods=["GET"])
@admin_required
def get_org_admins():
    """Get all organization administrators (UNCHANGED)"""
    try:
        admins = list(org_admins_collection.find({}, {"password": 0}).sort("organization", 1))
        for admin in admins:
            admin["_id"] = str(admin["_id"])
            if "added_at" in admin:
                admin["added_at"] = admin["added_at"].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify(admins), 200
    except Exception as e:
        print(f"Error fetching org admins: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/org-admins", methods=["POST"])
def add_org_admin():
    """Manually add an organization administrator (UNCHANGED)"""
    try:
        data = request.json
        required_fields = ["username", "email", "organization", "full_name"]
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if admin already exists
        existing_admin = org_admins_collection.find_one({
            "$or": [
                {"email": data["email"]},
                {"username": data["username"]}
            ]
        })
        
        if existing_admin:
            return jsonify({"error": "Admin with this email or username already exists"}), 400
        
        admin_data = {
            "username": data["username"],
            "full_name": data["full_name"],
            "email": data["email"],
            "organization": data["organization"],
            "role": data.get("role", "admin"),
            "added_at": get_ist_time(),
            "is_active": True
        }
        
        result = org_admins_collection.insert_one(admin_data)
        
        return jsonify({
            "message": "Organization admin added successfully",
            "admin_id": str(result.inserted_id)
        }), 201
        
    except Exception as e:
        print(f"Error adding org admin: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/org-admins/<admin_id>", methods=["DELETE"])
def remove_org_admin(admin_id):
    """Remove an organization administrator (UNCHANGED)"""
    try:
        result = org_admins_collection.delete_one({"_id": ObjectId(admin_id)})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Admin not found"}), 404
            
        return jsonify({"message": "Organization admin removed successfully"}), 200
        
    except Exception as e:
        print(f"Error removing org admin: {e}")
        return jsonify({"error": "Internal server error"}), 500



@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Handles submission of feedback text and an optional screenshot. (UNCHANGED)
    """
    
    # 1. Get Text Feedback and User Email from form data
    feedback_text = request.form.get('feedbackText', '').strip()
    user_email = request.form.get('userEmail', 'anonymous@app.com').strip() # Get email from form data
    IST = ZoneInfo("Asia/Kolkata") 
    submission_time = datetime.now(IST)
    # 2. Get Optional File Upload (screenshot)
    screenshot_file = request.files.get('screenshot')

    if not feedback_text and not screenshot_file:
        return jsonify({"message": "Feedback text or a screenshot is required."}), 400

    # 3. Handle File Upload (if present)
    file_path = None
    if screenshot_file:
        if screenshot_file.filename == '':
            pass 
        elif not allowed_file(screenshot_file.filename):
            return jsonify({"message": "Invalid file type. Only PNG, JPG, JPEG, GIF allowed."}), 400
        else:
            try:
                filename = secure_filename(screenshot_file.filename)
                # Ensure filename uniqueness
                filename_base, file_ext = os.path.splitext(filename)
                unique_filename = f"{filename_base}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"

                full_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                screenshot_file.save(full_path)
                file_path = unique_filename # Store only the unique filename in the DB
            except Exception as e:
                print(f"Error saving file: {e}")
                return jsonify({"message": "Failed to save screenshot."}), 500
    
    # 4. Insert into MongoDB feedback_collection
    feedback_doc = {
        "email": user_email,
        "feedback_text": feedback_text,
        "file_path": file_path, # File name if uploaded, None otherwise
        "time": submission_time,
        "is_reviewed": False 
    }
    
    result = feedback_collection.insert_one(feedback_doc)

    print(f"\n--- NEW FEEDBACK SUBMISSION SAVED ---")
    print(f"ID: {result.inserted_id}")
    print(f"Email: {user_email}")
    print(f"Text: {feedback_text}")
    print(f"File: {file_path}")
    print("---------------------------------")

    return jsonify({"message": "Feedback submitted successfully and saved for review."}), 200

@app.route("/admin/feedbacks", methods=["GET"])
@admin_required
def get_all_feedbacks():
    """Fetches all stored feedback for the admin dashboard. (UNCHANGED)"""
    try:
        feedbacks_cursor = feedback_collection.find().sort("time", -1) 
        
        feedbacks_list = []
        for feedback in feedbacks_cursor:
            feedback_data = {
                "id": str(feedback["_id"]),
                "email": feedback.get("email", "anonymous@example.com"),
                "feedback": feedback.get("feedback_text", "[No text]"),
                "file": feedback.get("file_path", "None"),
                "time": feedback.get("time", get_ist_time()).strftime('%Y-%m-%d %H:%M:%S UTC'),
                "is_reviewed": feedback.get("is_reviewed", False)
            }
            feedbacks_list.append(feedback_data)
            
        return jsonify(feedbacks_list), 200
        
    except Exception as e:
        print(f"Error fetching all feedbacks: {e}")
        return jsonify({"error": "Internal server error while fetching feedbacks"}), 500

@app.route("/admin/feedbacks/<feedback_id>/review", methods=["PUT"])
@admin_required
def mark_feedback_reviewed(feedback_id):
    """Marks a specific feedback item as reviewed. (UNCHANGED)"""
    try:
        result = feedback_collection.update_one(
            {"_id": ObjectId(feedback_id)},
            {"$set": {"is_reviewed": True}}
        )
        if result.matched_count == 0:
            return jsonify({"message": "Feedback not found."}), 404
        
        return jsonify({"message": "Feedback marked as reviewed successfully."}), 200
    except Exception as e:
        print(f"Error marking feedback as reviewed: {e}")
        return jsonify({"error": "Internal server error."}), 500


# Add this route to your app.py
@app.route("/admin/feedbacks/<feedback_id>", methods=["DELETE"])
@admin_required
def delete_feedback(feedback_id):
    """Delete a specific feedback item. (UNCHANGED)"""
    try:
        # Find the feedback to get file path for cleanup
        feedback = feedback_collection.find_one({"_id": ObjectId(feedback_id)})
        if not feedback:
            return jsonify({"message": "Feedback not found."}), 404
        
        # Delete associated file if exists
        file_path = feedback.get("file_path")
        if file_path and file_path != "None":
            try:
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as file_error:
                print(f"Error deleting feedback file: {file_error}")
        
        # Delete the feedback document
        result = feedback_collection.delete_one({"_id": ObjectId(feedback_id)})
        
        if result.deleted_count == 0:
            return jsonify({"message": "Feedback not found."}), 404
        
        return jsonify({"message": "Feedback deleted successfully."}), 200
    except Exception as e:
        print(f"Error deleting feedback: {e}")
        return jsonify({"error": "Internal server error."}), 500
    
@app.route("/login", methods=["POST"])
def login():
    """Handles user login and checks for approval status. Returns JWT token."""
    data = request.json
    username_or_email, password = data.get("username"), data.get("password")
    
    user = users_collection.find_one({"username": username_or_email})
    
    if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return jsonify({"message": "Invalid credentials"}), 401
    
    user_role = user.get("role", "user").lower()
    is_approved = user.get("is_approved", False)
    
    # --- NEW Approval Check Logic ---
    
    # 1. Developer Role Check (Only Developers and approved Admins/Users/Reviewers can proceed)
    # The Developer role is the highest level, and while their registration is pending, 
    # they shouldn't log in either.
    if not is_approved:
        # Check if the registration was explicitly rejected
        if user.get("is_rejected", False):
            return jsonify({"error": f"Account registration was rejected. Reason: {user.get('rejection_reason', 'Contact support.')}"}), 403

        # If not approved and not explicitly rejected, it's pending.
        if user_role == "developer":
            approval_target = "System Owner"
        elif user_role == "admin":
            approval_target = "Developer"
        else: # user/annotator/reviewer
            approval_target = "Admin"
            
        return jsonify({
            "error": "Account awaiting approval", 
            "message": f"Your account is pending approval by a {approval_target}."
        }), 403

    # --- End NEW Approval Check Logic ---

    # Generate JWT token (only runs if is_approved is True)
    token = generate_jwt_token(username_or_email, user_role)
    if not token:
        return jsonify({"message": "Failed to generate authentication token"}), 500
    
    log_action_and_update_report(username_or_email, 'Login')
    
    return jsonify({
        "message": "Login successful", 
        "username": username_or_email, 
        "role": user_role,
        "token": token, 
        "expires_in_hours": app.config['JWT_EXPIRATION_HOURS']
    })
    
@app.route("/refresh-token", methods=["POST"])
@token_required
def refresh_token():
    """Refresh JWT token"""
    try:
        current_user = request.current_user
        username = current_user.get('username')
        role = current_user.get('role')
        
        # Generate new token
        new_token = generate_jwt_token(username, role)
        if not new_token:
            return jsonify({"message": "Failed to generate new token"}), 500
        
        return jsonify({
            "message": "Token refreshed successfully",
            "token": new_token,
            "expires_in_hours": app.config['JWT_EXPIRATION_HOURS']
        }), 200
        
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return jsonify({"message": "Internal server error"}), 500

# Add these imports at the top if not already present
import random
import string

# OTP-based Password Reset Endpoints (UNCHANGED)

@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Send password reset OTP via email (UNCHANGED)"""
    try:
        data = request.json
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        # Check if user exists
        user = users_collection.find_one({"email": email})
        if not user:
            # Don't reveal whether email exists or not for security
            return jsonify({"message": "If an account with that email exists, an OTP has been sent to your email."}), 200
        
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        otp_expiry = get_ist_time() + timedelta(minutes=10)  # OTP valid for 10 minutes
        
        # Store OTP in database
        users_collection.update_one(
            {"email": email},
            {"$set": {
                "reset_otp": otp,
                "reset_otp_expiry": otp_expiry
            }}
        )
        
        # Send OTP email
        try:
            msg = Message(
                subject="Password Reset OTP - Sentence Annotation System",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            
            msg.body = f"""
Dear {user.get('full_name', 'User')},

You have requested to reset your password for the Sentence Annotation System.

Your One-Time Password (OTP) is: {otp}

This OTP will expire in 10 minutes.

If you did not request a password reset, please ignore this email.

Best regards,
Sentence Annotation System Team
"""
            mail.send(msg)
            print(f"Password reset OTP sent to: {email}")
            
        except Exception as e:
            print(f"Failed to send OTP email: {e}")
            return jsonify({"error": "Failed to send OTP email"}), 500
        
        return jsonify({"message": "If an account with that email exists, an OTP has been sent to your email."}), 200
        
    except Exception as e:
        print(f"Error in forgot password: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    """Verify OTP for password reset (UNCHANGED)"""
    try:
        data = request.json
        email = data.get("email")
        otp = data.get("otp")
        
        if not all([email, otp]):
            return jsonify({"error": "Email and OTP are required"}), 400
        
        # Find user with valid OTP
        user = users_collection.find_one({
            "email": email,
            "reset_otp": otp,
            "reset_otp_expiry": {"$gt": get_ist_time()}
        })
        
        if not user:
            return jsonify({"error": "Invalid or expired OTP"}), 400
        
        # Generate verification token for the reset session
        verification_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        # Store verification token
        users_collection.update_one(
            {"email": email},
            {"$set": {
                "reset_verified": True,
                "reset_verification_token": verification_token
            }}
        )
        
        return jsonify({
            "message": "OTP verified successfully",
            "verification_token": verification_token
        }), 200
        
    except Exception as e:
        print(f"Error verifying OTP: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/reset-password", methods=["POST"])
def reset_password():
    """Reset password using verified OTP session (UNCHANGED)"""
    try:
        data = request.json
        email = data.get("email")
        verification_token = data.get("verification_token")
        new_password = data.get("newPassword")
        
        if not all([email, verification_token, new_password]):
            return jsonify({"error": "All fields are required"}), 400
        
        # Verify the reset session
        user = users_collection.find_one({
            "email": email,
            "reset_verification_token": verification_token,
            "reset_verified": True
        })
        
        if not user:
            return jsonify({"error": "Invalid reset session. Please start over."}), 400
        
        # Hash new password
        hashed_pw = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
        
        # Update password and clear reset fields
        users_collection.update_one(
            {"email": email},
            {"$set": {
                "password": hashed_pw
            }, "$unset": {
                "reset_otp": "",
                "reset_otp_expiry": "",
                "reset_verified": "",
                "reset_verification_token": ""
            }}
        )
        
        # Send confirmation email
        try:
            msg = Message(
                subject="Password Reset Successful - Sentence Annotation System",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            
            msg.body = f"""
Dear {user.get('full_name', 'User')},

Your password has been successfully reset.

If you did not perform this action, please contact your administrator immediately.

Best regards,
Sentence Annotation System Team
"""
            mail.send(msg)
            print(f"Password reset confirmation sent to: {email}")
            
        except Exception as e:
            print(f"Failed to send password reset confirmation: {e}")
            # Don't return error here as password was still reset successfully
        
        # Log the action
        log_action_and_update_report(user["username"], "Password reset via OTP")
        
        return jsonify({"message": "Password reset successfully"}), 200
        
    except Exception as e:
        print(f"Error resetting password: {e}")
        return jsonify({"error": "Internal server error"}), 500
    

# --- NEW DEVELOPER ROUTE FOR APPROVAL ---

@app.route("/developer/pending-users", methods=["GET"])
@developer_required
def get_developer_pending_users():
    """
    Fetches all Admin and Developer users awaiting approval by a Developer.
    """
    try:
        # FIX: Fetches users with role 'admin' or 'developer' AND is_approved: False
        pending_users = list(users_collection.find({
            "role": {"$in": ["admin", "developer"]},
            "is_approved": False
        }, {"password": 0, "reset_otp": 0, "reset_otp_expiry": 0})) 

        for user in pending_users:
            user['_id'] = str(user['_id'])
            if 'registered_at' in user and isinstance(user['registered_at'], datetime):
                 user['registered_at'] = user['registered_at'].strftime('%Y-%m-%d %H:%M:%S')
            
        return jsonify({"pending_users": pending_users}), 200

    except Exception as e:
        print(f"Error fetching pending developer/admin users: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route("/developer/feedback", methods=["GET"])
@developer_required
def get_developer_feedback():
    """Fetches all submitted user feedback."""
    try:
        feedbacks_cursor = feedback_collection.find().sort("time", -1) 
        
        feedbacks_list = []
        for feedback in feedbacks_cursor:
            # FIX: Ensure field names match the FE viewer requirements (feedback_text, file_path)
            feedback_data = {
                "id": str(feedback["_id"]),
                "email": feedback.get("email", "anonymous@example.com"),
                "feedback_text": feedback.get("feedback_text", "[No text]"),
                "file_path": feedback.get("file_path", "None"),
                "time": feedback.get("time", get_ist_time()).strftime('%Y-%m-%d %H:%M:%S IST'),
                "is_reviewed": feedback.get("is_reviewed", False)
            }
            feedbacks_list.append(feedback_data)
        
        return jsonify({"feedbacks": feedbacks_list}), 200
        
    except Exception as e:
        print(f"Error fetching feedback for developer: {e}")
        return jsonify({"error": "Internal server error while fetching feedbacks"}), 500


    
# --- NEW ADMIN ROUTES FOR APPROVAL (UNCHANGED) ---

@app.route("/admin/pending-users", methods=["GET"])
@admin_required
def get_pending_users():
    """Fetches list of users who are not yet approved and not rejected (excluding admins)."""
    try:
        # Only show non-admin users pending approval AND not rejected
        pending_users_cursor = users_collection.find(
            {
                "is_approved": False,
                "is_rejected": {"$ne": True},  # Exclude rejected users
                "role": {"$nin": ["admin"]}  # Exclude admin users
            },
            {
                "username": 1, 
                "full_name": 1, 
                "email": 1, 
                "role": 1, 
                "organization": 1, 
                "languages": 1,
                "registered_at": 1
            }
        ).sort("registered_at", 1)
        
        pending_list = []
        for user in pending_users_cursor:
            user['_id'] = str(user['_id'])
            if 'registered_at' in user:
                user['registered_at'] = user['registered_at'].strftime('%Y-%m-%d %H:%M:%S')
            pending_list.append(user)
            
        return jsonify(pending_list), 200
        
    except Exception as e:
        print(f"Error fetching pending users: {e}")
        return jsonify({"error": "Internal server error"}), 500
  
@app.route("/admin/approve-user/<user_id>", methods=["PUT"])
@admin_required
def approve_user(user_id):
    """Approves a specific user by ID with IST timestamps and actual admin email."""
    try:
        data = request.json
        admin_username = data.get("adminUsername")
        
        if not admin_username:
            return jsonify({"error": "Admin username is required"}), 400
        
        # Get admin user details to get the actual email
        admin_user = users_collection.find_one({"username": admin_username})
        if not admin_user:
            return jsonify({"error": "Admin user not found"}), 404
            
        admin_email = admin_user.get("email", admin_username)
        
        # Use IST timezone for all timestamps
        IST = ZoneInfo("Asia/Kolkata")
        approval_time_ist = datetime.now(IST)
        
        # First get the user document to verify it exists
        user_doc = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            return jsonify({"message": "User not found."}), 404
        
        # Update the user - set is_approved to True and clear any rejection flags
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "is_approved": True, 
                "approved_by": admin_email,
                "approved_at": approval_time_ist,
                "is_rejected": False,  # Clear rejection status if it was previously rejected
                "rejection_reason": None  # Clear rejection reason
            }}
        )
        
        if result.matched_count == 0:
            return jsonify({"message": "User not found."}), 404
        
        # Send approval email to user
        send_user_approval_email(user_doc, approved=True)
        
        log_action_and_update_report(admin_username, f'Approved user account for: {user_doc.get("username", "Unknown User")}.')
        
        return jsonify({"message": f"User {user_doc.get('username', 'Unknown User')} successfully approved."}), 200
        
    except Exception as e:
        print(f"Error approving user: {e}")
        return jsonify({"error": "Internal server error during approval"}), 500
    
@app.route("/admin/reject-user/<user_id>", methods=["PUT"])
@admin_required
def reject_user(user_id):
    """Rejects a specific user by ID with IST timestamps and actual admin email."""
    try:
        data = request.json
        admin_username = data.get("adminUsername")
        rejection_reason = data.get("rejectionReason", "No reason provided")
        
        if not admin_username:
            return jsonify({"error": "Admin username is required"}), 400
            
        # Get admin user details to get the actual email
        admin_user = users_collection.find_one({"username": admin_username})
        if not admin_user:
            return jsonify({"error": "Admin user not found"}), 404
            
        admin_email = admin_user.get("email", admin_username)
        
        user_doc = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            return jsonify({"message": "User not found."}), 404
        
        # Use IST timezone
        IST = ZoneInfo("Asia/Kolkata")
        rejection_time_ist = datetime.now(IST)
        
        # Update rejection info and flag
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "is_rejected": True,
                "rejection_reason": rejection_reason,
                "rejected_by": admin_email,  # Store actual admin email
                "rejected_at": rejection_time_ist,  # IST timestamp
                "is_approved": False  # Ensure this remains False
            }}
        )

        # Send rejection email
        send_user_approval_email(user_doc, approved=False)
        
        # Log action
        log_action_and_update_report(
            admin_username, 
            f"Rejected user account for: {user_doc.get('username', 'Unknown User')}. Reason: {rejection_reason}"
        )
        
        return jsonify({"message": f"User {user_doc.get('username', 'Unknown User')} successfully rejected."}), 200

    except Exception as e:
        print(f"Error rejecting user: {e}")
        return jsonify({"error": f"Internal server error during rejection: {str(e)}"}), 500

     

   
# --- Other Routes (Unchanged) ---
@app.route("/check-role", methods=["POST"])
def check_role():
    data = request.json
    username = data.get("username")
    user = users_collection.find_one({"username": username})
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Allow admin users regardless of approval status
    if user.get("role", "").lower() != "admin" and not user.get("is_approved", False):
        return jsonify({"role": "unapproved"}), 403 
        
    return jsonify({"role": user.get("role", "user")})


@app.route("/logout", methods=["POST"])
def logout():
    """Handles user logout - enhanced to ensure session closure"""
    try:
        data = request.json
        username = data.get("username")
        
        # Try to verify token, but don't fail if it's expired
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')['1']
        
        if token:
            # Try to verify, but continue even if token is invalid
            try:
                payload = verify_jwt_token(token)
                if payload:
                    request.current_user = payload
            except Exception as e:
                print(f"Token verification failed during logout: {e}")
                # Continue with logout even if token is invalid
        
        # Always log the logout action and force session update
        if username:
            log_action_and_update_report(username, 'Logout')
            # Force immediate session history update
            update_session_history_report(username)
            
        return jsonify({"message": "Logout successful"})
        
    except Exception as e:
        print(f"Error during logout: {e}")
        # Still return success to allow client-side cleanup
        return jsonify({"message": "Logout completed"})

@app.route('/api/users-list', methods=['GET'])
def get_users_list():
    try:
        # Get only approved non-admin users (include reviewers and annotators)
        users = users_collection.find({
            'is_approved': True, 
            'role': {'$ne': 'admin'}  # Only exclude admin, include reviewers and annotators
        }, {'username': 1, '_id': 0})
        
        user_list = [user['username'] for user in users]
        return jsonify(user_list), 200
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
@app.route("/api/user/<username>", methods=["GET"])
def get_user_data(username):
    try:
        user = users_collection.find_one(
            {"username": username}, 
            {"full_name": 1, "email": 1, "role": 1, "_id": 0}
        )
        if user:
            return jsonify(user), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return jsonify({"error": "Internal server error"}), 500

# --- Visualization & Analytics Endpoints (UNCHANGED) ---

@app.route("/api/analytics/NE-distribution", methods=["GET"])
@admin_required
def get_ne_distribution():
    """Get comprehensive NE analytics with enhanced metrics"""
    try:
        # Get optional filters from query parameters
        language = request.args.get("language")
        project_id = request.args.get("project_id")
        username = request.args.get("username")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        print(f"DEBUG: Analytics request - project_id: {project_id}")
        
        # Build comprehensive filter for tags
        tag_filter = {}
        if username:
            tag_filter["username"] = username
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                tag_filter["annotation_date"] = {"$gte": start_dt, "$lte": end_dt}
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Get filtered tags with enhanced data
        all_tags = list(tags_collection.find(tag_filter))
        print(f"DEBUG: Found {len(all_tags)} tags with filter: {tag_filter}")
        
        # Enhanced statistics with more metrics
        project_stats = {}
        ne_type_stats = {}
        language_stats = {}
        user_stats = {}
        time_stats = {}
        
        for tag in all_tags:
            tag_type = tag.get("tag", "Unknown")
            tag_user = tag.get("username", "Unknown")
            tag_text = tag.get("text", "").lower().strip()
            sentence_id = tag.get("source_sentence_id")
            annotation_date = tag.get("annotation_date")
            
            # Enhanced NE type statistics
            if tag_type not in ne_type_stats:
                ne_type_stats[tag_type] = {
                    "count": 0, 
                    "unique_words": set(),
                    "unique_users": set(),
                    "first_annotation": annotation_date,
                    "last_annotation": annotation_date
                }
            ne_type_stats[tag_type]["count"] += 1
            ne_type_stats[tag_type]["unique_words"].add(tag_text)
            ne_type_stats[tag_type]["unique_users"].add(tag_user)
            
            # Update date range
            if annotation_date:
                if ne_type_stats[tag_type]["first_annotation"] is None or annotation_date < ne_type_stats[tag_type]["first_annotation"]:
                    ne_type_stats[tag_type]["first_annotation"] = annotation_date
                if ne_type_stats[tag_type]["last_annotation"] is None or annotation_date > ne_type_stats[tag_type]["last_annotation"]:
                    ne_type_stats[tag_type]["last_annotation"] = annotation_date
            
            # Enhanced user statistics
            if tag_user not in user_stats:
                user_stats[tag_user] = {
                    "count": 0, 
                    "ne_types": set(),
                    "unique_phrases": set(),
                    "first_annotation": annotation_date,
                    "last_annotation": annotation_date
                }
            user_stats[tag_user]["count"] += 1
            user_stats[tag_user]["ne_types"].add(tag_type)
            user_stats[tag_user]["unique_phrases"].add(tag_text)
            
            # Time-based statistics (by month)
            if annotation_date:
                month_key = annotation_date.strftime("%Y-%m")
                if month_key not in time_stats:
                    time_stats[month_key] = {"count": 0, "users": set()}
                time_stats[month_key]["count"] += 1
                time_stats[month_key]["users"].add(tag_user)
            
            # Enhanced project and language statistics
            if sentence_id:
                sentence = sentences_collection.find_one({"_id": ObjectId(sentence_id)})
                if sentence:
                    project_id_from_sentence = sentence.get("project_id")
                    
                    project_name = "Unassigned / Unknown Project"
                    project_language = "Unknown"
                    
                    if project_id_from_sentence:
                        try:
                            project = projects_collection.find_one({"_id": ObjectId(project_id_from_sentence)})
                            if project:
                                project_name = project.get("name", "Unknown Project")
                                project_language = project.get("language", "Unknown")
                        except:
                            project = projects_collection.find_one({"_id": project_id_from_sentence})
                            if project:
                                project_name = project.get("name", "Unknown Project")
                                project_language = project.get("language", "Unknown")
                    
                    # Enhanced project stats
                    if project_name not in project_stats:
                        project_stats[project_name] = {
                            "count": 0,
                            "ne_types": set(),
                            "users": set(),
                            "language": project_language
                        }
                    project_stats[project_name]["count"] += 1
                    project_stats[project_name]["ne_types"].add(tag_type)
                    project_stats[project_name]["users"].add(tag_user)
                    
                    # Enhanced language stats
                    if project_language not in language_stats:
                        language_stats[project_language] = {
                            "count": 0, 
                            "ne_types": set(),
                            "projects": set(),
                            "users": set()
                        }
                    language_stats[project_language]["count"] += 1
                    language_stats[project_language]["ne_types"].add(tag_type)
                    language_stats[project_language]["projects"].add(project_name)
                    language_stats[project_language]["users"].add(tag_user)
        
        # Convert to enhanced response format
        project_distribution = []
        for project_name, stats in project_stats.items():
            project_distribution.append({
                "project_name": project_name,
                "language": stats.get("language", "Unknown"),
                "count": stats["count"],
                "ne_type_count": len(stats["ne_types"]),
                "user_count": len(stats["users"]),
                "ne_types": list(stats["ne_types"])[:10]  # Top 10 NE types
            })
        
        ne_types_distribution = []
        for ne_type, stats in ne_type_stats.items():
            ne_types_distribution.append({
                "ne_type": ne_type,
                "count": stats["count"],
                "unique_word_count": len(stats["unique_words"]),
                "unique_user_count": len(stats["unique_users"]),
                "first_annotation": stats["first_annotation"].isoformat() if stats["first_annotation"] else None,
                "last_annotation": stats["last_annotation"].isoformat() if stats["last_annotation"] else None,
                "avg_per_user": stats["count"] / max(len(stats["unique_users"]), 1)
            })
        
        language_distribution = []
        for lang, stats in language_stats.items():
            language_distribution.append({
                "language": lang,
                "count": stats["count"],
                "ne_type_count": len(stats["ne_types"]),
                "project_count": len(stats["projects"]),
                "user_count": len(stats["users"])
            })
        
        user_distribution = []
        for user, stats in user_stats.items():
            user_distribution.append({
                "username": user,
                "count": stats["count"],
                "ne_type_count": len(stats["ne_types"]),
                "unique_phrase_count": len(stats["unique_phrases"]),
                "first_annotation": stats["first_annotation"].isoformat() if stats["first_annotation"] else None,
                "last_annotation": stats["last_annotation"].isoformat() if stats["last_annotation"] else None,
                "productivity_score": stats["count"] / max(len(stats["ne_types"]), 1)
            })
        
        # Time distribution
        time_distribution = []
        for month, stats in sorted(time_stats.items()):
            time_distribution.append({
                "month": month,
                "count": stats["count"],
                "active_users": len(stats["users"])
            })
        
        # Overall summary statistics
        total_users = len(user_stats)
        total_projects = len(project_stats)
        total_languages = len(language_stats)
        total_ne_types = len(ne_type_stats)
        
        avg_annotations_per_user = len(all_tags) / max(total_users, 1)
        avg_ne_types_per_user = sum(len(stats["ne_types"]) for stats in user_stats.values()) / max(total_users, 1)
        
        print(f"DEBUG: Enhanced analytics processed - Tags: {len(all_tags)}, Users: {total_users}, Projects: {total_projects}")
        
        return jsonify({
            "summary": {
                "total_annotations": len(all_tags),
                "total_users": total_users,
                "total_projects": total_projects,
                "total_languages": total_languages,
                "total_ne_types": total_ne_types,
                "avg_annotations_per_user": round(avg_annotations_per_user, 2),
                "avg_ne_types_per_user": round(avg_ne_types_per_user, 2),
                "time_period": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            "ne_types": sorted(ne_types_distribution, key=lambda x: x["count"], reverse=True),
            "language_distribution": sorted(language_distribution, key=lambda x: x["count"], reverse=True),
            "user_distribution": sorted(user_distribution, key=lambda x: x["count"], reverse=True),
            "project_distribution": sorted(project_distribution, key=lambda x: x["count"], reverse=True),
            "time_distribution": time_distribution,
            "top_performers": sorted(user_distribution, key=lambda x: x["count"], reverse=True)[:10],
            "most_common_ne": sorted(ne_types_distribution, key=lambda x: x["count"], reverse=True)[:10]
        }), 200
        
    except Exception as e:
        print(f"Error in enhanced NE distribution: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500
    
      
@app.route("/api/analytics/ne-network", methods=["GET"])
def get_ne_network():
    """Generate network data for NE relationships"""
    try:
        # Get all NE annotations
        all_tags = list(tags_collection.find({}, {
            "text": 1, 
            "tag": 1, 
            "username": 1,
            "source_sentence_id": 1
        }))
        
        nodes = []
        links = []
        node_ids = {}
        node_counter = 0
        
        # Helper function to add or get node ID
        def get_node_id(text, ne_type):
            nonlocal node_counter
            key = f"{text}_{ne_type}"
            if key not in node_ids:
                node_ids[key] = node_counter
                nodes.append({
                    "id": node_counter,
                    "name": text,
                    "ne_type": ne_type,
                    "value": 1  # Will be updated with frequency
                })
                node_counter += 1
            return node_ids[key]
        
        # First pass: create nodes and count frequencies
        for tag in all_tags:
            text = tag.get("text", "").strip().lower()
            ne_type = tag.get("tag", "Unknown")
            if text:
                node_id = get_node_id(text, ne_type)
                nodes[node_id]["value"] += 1
        
        # Second pass: create links based on shared roots and relationships
        ne_by_type = {}
        for tag in all_tags:
            text = tag.get("text", "").strip().lower()
            ne_type = tag.get("tag", "Unknown")
            if text and ne_type:
                if ne_type not in ne_by_type:
                    ne_by_type[ne_type] = []
                ne_by_type[ne_type].append(text)
        
        # Create links within same NE types (clustering)
        for ne_type, words in ne_by_type.items():
            # Simple stemming-based relationships
            word_stems = {}
            for word in words:
                # Basic stemming: take first 4 characters as stem
                stem = word[:4].lower()
                if stem not in word_stems:
                    word_stems[stem] = []
                word_stems[stem].append(word)
            
            # Create links for words sharing the same stem
            for stem, stem_words in word_stems.items():
                if len(stem_words) > 1:
                    # Create a complete graph for words sharing the same stem
                    for i, word1 in enumerate(stem_words):
                        for word2 in stem_words[i+1:]:
                            if word1 != word2:
                                source_id = get_node_id(word1, ne_type)
                                target_id = get_node_id(word2, ne_type)
                                
                                # Check if link already exists
                                existing_link = next(
                                    (link for link in links 
                                     if link["source"] == source_id and link["target"] == target_id),
                                    None
                                )
                                
                                if existing_link:
                                    existing_link["value"] += 1
                                else:
                                    links.append({
                                        "source": source_id,
                                        "target": target_id,
                                        "value": 1,
                                        "type": "shared_stem"
                                    })
        
        # Add some random layout positions for visualization
        for node in nodes:
            node["x"] = np.random.random() * 100 if 'np' in globals() else random.random() * 100
            node["y"] = np.random.random() * 100 if 'np' in globals() else random.random() * 100
        
        return jsonify({
            "nodes": nodes,
            "links": links,
            "total_nodes": len(nodes),
            "total_links": len(links)
        }), 200
        
    except Exception as e:
        print(f"Error generating NE network: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/analytics/annotation-timeline", methods=["GET"])
def get_annotation_timeline():
    """Get annotation timeline data for the last 30 days"""
    try:
        # Get optional filters
        language = request.args.get("language")
        project_id = request.args.get("project_id")
        username = request.args.get("username")
        
        # Build match filter
        match_filter = {}
        if username:
            match_filter["username"] = username
        
        # If project_id is provided, filter by project sentences
        if project_id:
            project_sentences = list(sentences_collection.find(
                {"project_id": project_id}, 
                {"_id": 1}
            ))
            sentence_ids = [str(s["_id"]) for s in project_sentences]
            if sentence_ids:
                match_filter["source_sentence_id"] = {"$in": sentence_ids}
        
        # Calculate date range (last 30 days)
        end_date = get_ist_time()
        start_date = end_date - timedelta(days=30)
        
        match_filter["annotation_date"] = {"$gte": start_date, "$lte": end_date}
        
        # Aggregate timeline data by date
        pipeline = [
            {"$match": match_filter},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$annotation_date"
                    }
                },
                "count": {"$sum": 1},
                "unique_annotators": {"$addToSet": "$username"}
            }},
            {"$project": {
                "date": "$_id",
                "count": 1,
                "unique_annotators_count": {"$size": "$unique_annotators"},
                "_id": 0
            }},
            {"$sort": {"date": 1}}
        ]
        
        timeline_data = list(tags_collection.aggregate(pipeline))
        
        # Fill in missing dates with zeros
        filled_timeline = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            existing_data = next((item for item in timeline_data if item["date"] == date_str), None)
            
            if existing_data:
                filled_timeline.append(existing_data)
            else:
                filled_timeline.append({
                    "date": date_str,
                    "count": 0,
                    "unique_annotators_count": 0
                })
            
            current_date += timedelta(days=1)
        
        return jsonify(filled_timeline), 200
        
    except Exception as e:
        print(f"Error fetching annotation timeline: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/analytics/reports/download", methods=["GET"])
def download_analytics_report():
    """Download comprehensive analytics report with enhanced data"""
    try:
        report_type = request.args.get("type", "csv")  # csv or pdf
        language = request.args.get("language")
        project_id = request.args.get("project_id")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        detail_level = request.args.get("detail", "summary")  # summary, detailed, comprehensive
        
        print(f"DEBUG: Enhanced download report - type: {report_type}, project_id: {project_id}")
        
        # Build comprehensive filter
        tag_filter = {}
        if language:
            tag_filter["language"] = language
        if project_id:
            project_sentences = list(sentences_collection.find(
                {"project_id": project_id}, 
                {"_id": 1}
            ))
            sentence_ids = [str(s["_id"]) for s in project_sentences]
            if sentence_ids:
                tag_filter["source_sentence_id"] = {"$in": sentence_ids}
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                tag_filter["annotation_date"] = {"$gte": start_dt, "$lte": end_dt}
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        print(f"DEBUG: Enhanced filter for report: {tag_filter}")
        
        # Get comprehensive data
        all_tags = list(tags_collection.find(tag_filter))
        print(f"DEBUG: Found {len(all_tags)} tags for enhanced report")
        
        # Enhanced sentence statistics
        pipeline = [
            {"$group": {
                "_id": {
                    "project_id": "$project_id", 
                    "original_index": "$original_index"
                },
                "is_annotated_status": {"$max": {"$cond": ["$is_annotated", 1, 0]}},
                "project_id": {"$first": "$project_id"},
                "usernames": {"$addToSet": "$username"}
            }},
            {"$group": {
                "_id": None,
                "total_unique_sentences": {"$sum": 1},
                "total_annotated": {"$sum": "$is_annotated_status"},
                "total_annotators": {"$addToSet": "$usernames"}
            }},
            {"$project": {
                "total_unique_sentences": 1,
                "total_annotated": 1,
                "total_annotators": {"$size": {"$reduce": {
                    "input": "$total_annotators",
                    "initialValue": [],
                    "in": {"$setUnion": ["$$value", "$$this"]}
                }}}
            }}
        ]
        
        stats_result = list(sentences_collection.aggregate(pipeline))
        if stats_result:
            stats = stats_result[0]
            total_sentences = stats.get("total_unique_sentences", 0)
            annotated_sentences = stats.get("total_annotated", 0)
            total_annotators = stats.get("total_annotators", 0)
        else:
            total_sentences = 0
            annotated_sentences = 0
            total_annotators = 0

        # Enhanced user statistics
        user_stats = []
        all_users = list(users_collection.find({}))
        
        for user in all_users:
            username = user["username"]
            
            # User sentence statistics
            user_sentences_pipeline = [
                {"$match": {"username": username}},
                {"$group": {
                    "_id": {
                        "project_id": "$project_id", 
                        "original_index": "$original_index"
                    },
                    "is_annotated_status": {"$max": {"$cond": ["$is_annotated", 1, 0]}}
                }},
                {"$group": {
                    "_id": None,
                    "total_sentences": {"$sum": 1},
                    "annotated_sentences": {"$sum": "$is_annotated_status"}
                }}
            ]
            
            user_sentences_result = list(sentences_collection.aggregate(user_sentences_pipeline))
            if user_sentences_result:
                user_sentences_stats = user_sentences_result[0]
                user_total_sentences = user_sentences_stats.get("total_sentences", 0)
                user_annotated_sentences = user_sentences_stats.get("annotated_sentences", 0)
            else:
                user_total_sentences = 0
                user_annotated_sentences = 0
            
            # User tag statistics
            user_tags = list(tags_collection.find({"username": username}))
            user_tags_count = len(user_tags)
            
            # User NE type diversity
            user_ne_types = set(tag.get("tag", "Unknown") for tag in user_tags)
            
            # Calculate enhanced metrics
            approval_rate = (user_annotated_sentences / user_total_sentences * 100) if user_total_sentences > 0 else 0
            productivity_score = user_tags_count / max(len(user_ne_types), 1)
            
            user_stats.append({
                "username": username,
                "full_name": user.get("full_name", "N/A"),
                "role": user.get("role", "N/A"),
                "organization": user.get("organization", "N/A"),
                "total_sentences": user_total_sentences,
                "annotated_sentences": user_annotated_sentences,
                "total_annotations": user_tags_count,
                "ne_type_diversity": len(user_ne_types),
                "approval_rate": round(approval_rate, 1),
                "productivity_score": round(productivity_score, 2),
                "status": "Active" if user_tags_count > 0 else "Inactive"
            })

        # Enhanced NE type statistics
        ne_stats = []
        ne_type_counts = {}
        
        for tag in all_tags:
            ne_type = tag.get("tag", "Unknown")
            if ne_type not in ne_type_counts:
                ne_type_counts[ne_type] = {
                    "count": 0,
                    "unique_phrases": set(),
                    "unique_annotators": set(),
                    "projects": set(),
                    "first_annotation": tag.get("annotation_date"),
                    "last_annotation": tag.get("annotation_date")
                }
            ne_type_counts[ne_type]["count"] += 1
            ne_type_counts[ne_type]["unique_phrases"].add(tag.get("text", "").lower())
            ne_type_counts[ne_type]["unique_annotators"].add(tag.get("username", ""))
            
            # Track projects
            if tag.get("source_sentence_id"):
                sentence = sentences_collection.find_one({"_id": ObjectId(tag["source_sentence_id"])})
                if sentence and sentence.get("project_id"):
                    ne_type_counts[ne_type]["projects"].add(sentence["project_id"])
            
            # Update date range
            annotation_date = tag.get("annotation_date")
            if annotation_date:
                if ne_type_counts[ne_type]["first_annotation"] is None or annotation_date < ne_type_counts[ne_type]["first_annotation"]:
                    ne_type_counts[ne_type]["first_annotation"] = annotation_date
                if ne_type_counts[ne_type]["last_annotation"] is None or annotation_date > ne_type_counts[ne_type]["last_annotation"]:
                    ne_type_counts[ne_type]["last_annotation"] = annotation_date
        
        for ne_type, stats in ne_type_counts.items():
            ne_stats.append({
                "ne_type": ne_type,
                "count": stats["count"],
                "unique_phrases_count": len(stats["unique_phrases"]),
                "unique_annotators_count": len(stats["unique_annotators"]),
                "project_count": len(stats["projects"]),
                "first_annotation": stats["first_annotation"].strftime("%Y-%m-%d") if stats["first_annotation"] else "N/A",
                "last_annotation": stats["last_annotation"].strftime("%Y-%m-%d") if stats["last_annotation"] else "N/A",
                "popularity_rank": "High" if stats["count"] > 100 else "Medium" if stats["count"] > 50 else "Low"
            })

        # Enhanced project statistics
        project_stats = []
        all_projects = list(projects_collection.find({}))
        
        for project in all_projects:
            project_id_str = str(project["_id"])
            project_name = project.get("name", "Unknown Project")
            
            # Project sentence statistics
            project_sentences_pipeline = [
                {"$match": {"project_id": project_id_str}},
                {"$group": {
                    "_id": {
                        "project_id": "$project_id", 
                        "original_index": "$original_index"
                    },
                    "is_annotated_status": {"$max": {"$cond": ["$is_annotated", 1, 0]}},
                    "project_id": {"$first": "$project_id"},
                    "usernames": {"$addToSet": "$username"}
                }},
                {"$group": {
                    "_id": None,
                    "total_unique_sentences": {"$sum": 1},
                    "total_annotated": {"$sum": "$is_annotated_status"},
                    "total_annotators": {"$addToSet": "$usernames"}
                }},
                {"$project": {
                    "total_unique_sentences": 1,
                    "total_annotated": 1,
                    "total_annotators": {
                        "$size": {
                            "$reduce": {
                                "input": "$total_annotators",
                                "initialValue": [],
                                "in": {"$setUnion": ["$$value", "$$this"]}
                            }
                        }
                    }
                }}
            ]
            
            project_sentences_result = list(sentences_collection.aggregate(project_sentences_pipeline))
            if project_sentences_result:
                project_sentences_stats = project_sentences_result[0]
                project_total_sentences = project_sentences_stats.get("total_sentences", 0)
                project_annotated_sentences = project_sentences_stats.get("annotated_sentences", 0)
                project_annotators = project_sentences_stats.get("total_annotators", 0)
            else:
                project_total_sentences = 0
                project_annotated_sentences = 0
                project_annotators = 0
            
            # Project tag statistics
            project_tags_count = tags_collection.count_documents({
                "source_sentence_id": {"$in": [str(s["_id"]) for s in sentences_collection.find({"project_id": project_id_str}, {"_id": 1})]}
            })
            
            completion_rate = (project_annotated_sentences / project_total_sentences * 100) if project_total_sentences > 0 else 0
            annotation_density = (project_tags_count / project_total_sentences) if project_total_sentences > 0 else 0
            
            project_stats.append({
                "project_name": project_name,
                "language": project.get("language", "Unknown"),
                "total_sentences": project_total_sentences,
                "annotated_sentences": project_annotated_sentences,
                "total_annotations": project_tags_count,
                "total_annotators": project_annotators,
                "completion_rate": round(completion_rate, 1),
                "annotation_density": round(annotation_density, 2),
                "status": "Completed" if completion_rate == 100 else "In Progress" if completion_rate > 0 else "Not Started",
                "created_date": project.get("created_at", get_ist_time()).strftime("%Y-%m-%d") if project.get("created_at") else "N/A"
            })

        print(f"DEBUG: Enhanced report statistics - Sentences: {total_sentences}/{annotated_sentences}, Users: {len(user_stats)}, Projects: {len(project_stats)}")

        if report_type.lower() == "csv":
            # Generate enhanced CSV report
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Report header with enhanced metadata
            writer.writerow(["SENTENCE ANNOTATION SYSTEM - COMPREHENSIVE ANALYTICS REPORT"])
            writer.writerow(["Generated on:", get_ist_time().strftime("%Y-%m-%d %H:%M:%S UTC")])
            writer.writerow(["Report Period:", f"{start_date} to {end_date}" if start_date and end_date else "All Time"])
            writer.writerow(["Detail Level:", detail_level])
            writer.writerow([])
            
            # Executive Summary
            writer.writerow(["EXECUTIVE SUMMARY"])
            writer.writerow(["Total Sentences", total_sentences])
            writer.writerow(["Annotated Sentences", annotated_sentences])
            writer.writerow(["Annotation Rate", f"{(annotated_sentences/total_sentences*100):.1f}%" if total_sentences > 0 else "0%"])
            writer.writerow(["Total Annotations", len(all_tags)])
            writer.writerow(["Total Annotators", total_annotators])
            writer.writerow(["Total Projects", len(project_stats)])
            writer.writerow(["Average Annotations per User", f"{(len(all_tags)/max(total_annotators, 1)):.1f}"])
            writer.writerow([])
            
            if detail_level in ["detailed", "comprehensive"]:
                # User Performance Dashboard
                writer.writerow(["USER PERFORMANCE DASHBOARD"])
                writer.writerow(["Username", "Full Name", "Role", "Organization", "Total Sentences", "Annotated Sentences", "Total Annotations", "NE Diversity", "Approval Rate", "Productivity Score", "Status"])
                for user in sorted(user_stats, key=lambda x: x["total_annotations"], reverse=True):
                    writer.writerow([
                        user["username"],
                        user["full_name"],
                        user["role"],
                        user["organization"],
                        user["total_sentences"],
                        user["annotated_sentences"],
                        user["total_annotations"],
                        user["ne_type_diversity"],
                        f"{user['approval_rate']}%",
                        user["productivity_score"],
                        user["status"]
                    ])
                writer.writerow([])
            
            # NE Statistics
            writer.writerow(["NE TYPE STATISTICS"])
            writer.writerow(["NE Type", "Count", "Unique Phrases", "Unique Annotators", "Projects", "First Annotation", "Last Annotation", "Popularity"])
            for ne in sorted(ne_stats, key=lambda x: x["count"], reverse=True):
                writer.writerow([
                    ne["ne_type"],
                    ne["count"],
                    ne["unique_phrases_count"],
                    ne["unique_annotators_count"],
                    ne["project_count"],
                    ne["first_annotation"],
                    ne["last_annotation"],
                    ne["popularity_rank"]
                ])
            writer.writerow([])
            
            # Project Statistics
            writer.writerow(["PROJECT STATISTICS"])
            writer.writerow(["Project Name", "Language", "Total Sentences", "Annotated Sentences", "Total Annotations", "Annotators", "Completion Rate", "Annotation Density", "Status", "Created Date"])
            for project in sorted(project_stats, key=lambda x: x["completion_rate"], reverse=True):
                writer.writerow([
                    project["project_name"],
                    project["language"],
                    project["total_sentences"],
                    project["annotated_sentences"],
                    project["total_annotations"],
                    project["total_annotators"],
                    f"{project['completion_rate']}%",
                    project["annotation_density"],
                    project["status"],
                    project["created_date"]
                ])
            
            if detail_level == "comprehensive":
                writer.writerow([])
                writer.writerow(["DETAILED ANNOTATION DATA"])
                writer.writerow(["Annotation ID", "NE Type", "Phrase", "Annotator", "Project", "Sentence Text Preview", "Annotation Date"])
                for i, tag in enumerate(all_tags[:1000]):  # Limit to first 1000 for file size
                    sentence_text = "N/A"
                    project_name = "N/A"
                    if tag.get("source_sentence_id"):
                        sentence = sentences_collection.find_one({"_id": ObjectId(tag["source_sentence_id"])})
                        if sentence:
                            sentence_text = sentence.get("textContent", "N/A")[:50] + "..." if len(sentence.get("textContent", "")) > 50 else sentence.get("textContent", "N/A")
                            if sentence.get("project_id"):
                                project = projects_collection.find_one({"_id": ObjectId(sentence["project_id"])})
                                if project:
                                    project_name = project.get("name", "N/A")
                    
                    writer.writerow([
                        str(tag["_id"]),
                        tag.get("tag", "Unknown"),
                        tag.get("text", "N/A"),
                        tag.get("username", "Unknown"),
                        project_name,
                        sentence_text,
                        tag.get("annotation_date", get_ist_time()).strftime("%Y-%m-%d") if tag.get("annotation_date") else "N/A"
                    ])
            
            response = Response(output.getvalue(), mimetype='text/csv')
            response.headers["Content-Disposition"] = f"attachment; filename=comprehensive_annotation_report_{get_ist_time().strftime('%Y%m%d_%H%M%S')}.csv"
            return response
            
        else:
            # Enhanced JSON response for PDF/other formats
            return jsonify({
                "report_metadata": {
                    "generated_at": get_ist_time().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "report_type": "comprehensive",
                    "period": f"{start_date} to {end_date}" if start_date and end_date else "All Time",
                    "filters_applied": {
                        "language": language,
                        "project_id": project_id,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                },
                "executive_summary": {
                    "total_sentences": total_sentences,
                    "annotated_sentences": annotated_sentences,
                    "annotation_rate": round((annotated_sentences/total_sentences*100), 1) if total_sentences > 0 else 0,
                    "total_annotations": len(all_tags),
                    "total_annotators": total_annotators,
                    "total_projects": len(project_stats),
                    "avg_annotations_per_user": round((len(all_tags)/max(total_annotators, 1)), 1)
                },
                "user_performance": sorted(user_stats, key=lambda x: x["total_annotations"], reverse=True),
                "ne_statistics": sorted(ne_stats, key=lambda x: x["count"], reverse=True),
                "project_statistics": sorted(project_stats, key=lambda x: x["completion_rate"], reverse=True),
                "key_insights": {
                    "top_performer": max(user_stats, key=lambda x: x["total_annotations"]) if user_stats else None,
                    "most_common_ne": max(ne_stats, key=lambda x: x["count"]) if ne_stats else None,
                    "most_complete_project": max(project_stats, key=lambda x: x["completion_rate"]) if project_stats else None,
                    "annotation_trend": "Growing" if len(all_tags) > 1000 else "Stable" if len(all_tags) > 500 else "Developing"
                }
            }), 200
            
    except Exception as e:
        print(f"Error generating enhanced analytics report: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500
      
@app.route("/api/analytics/reports/pdf-with-charts", methods=["GET"])
@admin_required
def download_pdf_with_charts():
    """Generate PDF report with embedded charts and visualizations"""
    try:
        # Get filter parameters
        language = request.args.get("language")
        project_id = request.args.get("project_id")
        username = request.args.get("username")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        # Build filter for tags (same as existing analytics)
        tag_filter = {}
        if username:
            tag_filter["username"] = username
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                tag_filter["annotation_date"] = {"$gte": start_dt, "$lte": end_dt}
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Get all the analytics data needed for charts
        all_tags = list(tags_collection.find(tag_filter))
        
        # Calculate statistics (same as your existing analytics logic)
        project_stats = {}
        ne_type_stats = {}
        language_stats = {}
        user_stats = {}
        
        for tag in all_tags:
            tag_type = tag.get("tag", "Unknown")
            tag_user = tag.get("username", "Unknown")
            sentence_id = tag.get("source_sentence_id")
            
            # Count by NE type
            if tag_type not in ne_type_stats:
                ne_type_stats[tag_type] = {"count": 0, "unique_words": set()}
            ne_type_stats[tag_type]["count"] += 1
            ne_type_stats[tag_type]["unique_words"].add(tag.get("text", "").lower())
            
            # Count by user
            if tag_user not in user_stats:
                user_stats[tag_user] = {"count": 0, "ne_types": set()}
            user_stats[tag_user]["count"] += 1
            user_stats[tag_user]["ne_types"].add(tag_type)
            
            # Count by project and language
            if sentence_id:
                sentence = sentences_collection.find_one({"_id": ObjectId(sentence_id)})
                if sentence:
                    project_id_from_sentence = sentence.get("project_id")
                    
                    project_name = "Unassigned / Unknown Project"
                    project_language = "Unknown"
                    
                    if project_id_from_sentence:
                        try:
                            project = projects_collection.find_one({"_id": ObjectId(project_id_from_sentence)})
                            if project:
                                project_name = project.get("name", "Unknown Project")
                                project_language = project.get("language", "Unknown")
                        except:
                            project = projects_collection.find_one({"_id": project_id_from_sentence})
                            if project:
                                project_name = project.get("name", "Unknown Project")
                                project_language = project.get("language", "Unknown")
                    
                    # Update project stats
                    if project_name not in project_stats:
                        project_stats[project_name] = {
                            "count": 0,
                            "ne_types": set()
                        }
                    project_stats[project_name]["count"] += 1
                    project_stats[project_name]["ne_types"].add(tag_type)
                    
                    # Update language stats
                    if project_language not in language_stats:
                        language_stats[project_language] = {"count": 0, "ne_types": set()}
                    language_stats[project_language]["count"] += 1
                    language_stats[project_language]["ne_types"].add(tag_type)
        
        # Convert to chart-ready formats
        ne_chart_data = []
        for ne_type, stats in ne_type_stats.items():
            ne_chart_data.append({
                "ne_type": ne_type,
                "count": stats["count"],
                "unique_word_count": len(stats["unique_words"])
            })
        
        language_chart_data = []
        for lang, stats in language_stats.items():
            language_chart_data.append({
                "language": lang,
                "count": stats["count"]
            })
        
        user_chart_data = []
        for user, stats in user_stats.items():
            user_chart_data.append({
                "username": user,
                "count": stats["count"],
                "ne_type_count": len(stats["ne_types"])
            })
        
        project_chart_data = []
        for project_name, stats in project_stats.items():
            project_chart_data.append({
                "project_name": project_name,
                "count": stats["count"],
                "ne_type_count": len(stats["ne_types"])
            })
        
        # Get timeline data
        timeline_data = []
        try:
            # Use your existing timeline logic
            end_date_tl = get_ist_time()
            start_date_tl = end_date_tl - timedelta(days=30)
            
            timeline_match_filter = {}
            if username:
                timeline_match_filter["username"] = username
            
            if project_id:
                project_sentences = list(sentences_collection.find(
                    {"project_id": project_id}, 
                    {"_id": 1}
                ))
                sentence_ids = [str(s["_id"]) for s in project_sentences]
                if sentence_ids:
                    timeline_match_filter["source_sentence_id"] = {"$in": sentence_ids}
            
            timeline_match_filter["annotation_date"] = {"$gte": start_date_tl, "$lte": end_date_tl}
            
            pipeline = [
                {"$match": timeline_match_filter},
                {"$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$annotation_date"
                        }
                    },
                    "count": {"$sum": 1},
                    "unique_annotators": {"$addToSet": "$username"}
                }},
                {"$project": {
                    "date": "$_id",
                    "count": 1,
                    "unique_annotators_count": {"$size": "$unique_annotators"},
                    "_id": 0
                }},
                {"$sort": {"date": 1}}
            ]
            
            timeline_raw = list(tags_collection.aggregate(pipeline))
            
            # Fill in missing dates
            current_date = start_date_tl
            while current_date <= end_date_tl:
                date_str = current_date.strftime("%Y-%m-%d")
                existing_data = next((item for item in timeline_raw if item["date"] == date_str), None)
                
                if existing_data:
                    timeline_data.append(existing_data)
                else:
                    timeline_data.append({
                        "date": date_str,
                        "count": 0,
                        "unique_annotators_count": 0
                    })
                
                current_date += timedelta(days=1)
                
        except Exception as e:
            print(f"Error generating timeline data: {e}")
        
        # Return comprehensive data for PDF generation
        return jsonify({
            "summary": {
                "total_annotations": len(all_tags),
                "total_ne_types": len(ne_type_stats),
                "total_languages": len(language_stats),
                "total_users": len(user_stats),
                "total_projects": len(project_stats),
                "report_generated": get_ist_time().strftime("%Y-%m-%d %H:%M:%S UTC")
            },
            "charts": {
                "ne_distribution": ne_chart_data,
                "language_distribution": language_chart_data,
                "user_distribution": user_chart_data,
                "project_distribution": project_chart_data,
                "timeline": timeline_data
            },
            "filters_applied": {
                "language": language,
                "project_id": project_id,
                "username": username,
                "start_date": start_date,
                "end_date": end_date
            }
        }), 200
        
    except Exception as e:
        print(f"Error generating PDF chart data: {e}")
        return jsonify({"error": "Internal server error"}), 500

import base64
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from matplotlib import style

@app.route("/api/analytics/generate-chart", methods=["POST"])
@admin_required
def generate_chart():
    """Generate professional charts for PDF reports"""
    try:
        data = request.json
        chart_type = data.get('type', 'bar')
        chart_data = data.get('data', [])
        title = data.get('title', 'Chart')
        x_label = data.get('x_label', '')
        y_label = data.get('y_label', 'Count')
        
        # Set professional style
        plt.style.use('seaborn-v0_8')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Prepare data
        labels = []
        values = []
        colors = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        for i, item in enumerate(chart_data):
            label_key = next((key for key in ['ne_type', 'language', 'username', 'project_name'] if key in item), 'label')
            value_key = next((key for key in ['count', 'value'] if key in item), 'value')
            
            labels.append(item.get(label_key, f'Item {i+1}'))
            values.append(item.get(value_key, 0))
        
        # Create chart based on type
        if chart_type == 'bar':
            bars = ax.bar(labels, values, color=colors[:len(labels)], alpha=0.8, edgecolor='black', linewidth=0.5)
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}', ha='center', va='bottom', fontweight='bold')
                
        elif chart_type == 'pie':
            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                             colors=colors[:len(labels)], startangle=90)
            # Style percentage text
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                
        elif chart_type == 'line':
            ax.plot(labels, values, marker='o', linewidth=2, markersize=6, color='#0088FE')
            ax.fill_between(labels, values, alpha=0.3, color='#0088FE')
        
        # Styling
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(x_label, fontweight='bold')
        ax.set_ylabel(y_label, fontweight='bold')
        
        # Rotate x-labels for better readability
        if chart_type in ['bar', 'line']:
            plt.xticks(rotation=45, ha='right')
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Remove spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        
        # Convert to base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{image_base64}',
            'image_data': image_base64  # For direct use in PDF
        })
        
    except Exception as e:
        print(f"Error generating chart: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/analytics/comprehensive-report", methods=["GET"])
@admin_required
def get_comprehensive_report():
    """Generate professional comprehensive report with enhanced analytics"""
    try:
        # Get filter parameters
        language = request.args.get("language")
        project_id = request.args.get("project_id")
        username = request.args.get("username")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        report_level = request.args.get("level", "standard")  # standard, detailed, executive
        
        # Build comprehensive analytics
        tag_filter = {}
        if username:
            tag_filter["username"] = username
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                tag_filter["annotation_date"] = {"$gte": start_dt, "$lte": end_dt}
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Enhanced analytics queries
        all_tags = list(tags_collection.find(tag_filter))
        total_annotations = len(all_tags)
        
        # Comprehensive user performance analytics
        user_performance = list(tags_collection.aggregate([
            {"$match": tag_filter},
            {"$group": {
                "_id": "$username",
                "total_annotations": {"$sum": 1},
                "unique_ne_types": {"$addToSet": "$tag"},
                "unique_phrases": {"$addToSet": "$text"},
                "projects": {"$addToSet": "$source_sentence_id"},
                "first_annotation": {"$min": "$annotation_date"},
                "last_annotation": {"$max": "$annotation_date"},
                "daily_average": {
                    "$avg": {
                        "$cond": [
                            {"$ne": ["$annotation_date", None]},
                            {"$divide": [
                                {"$subtract": [{"$max": "$annotation_date"}, {"$min": "$annotation_date"}]},
                                1000 * 60 * 60 * 24  # Convert to days
                            ]},
                            0
                        ]
                    }
                }
            }},
            {"$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "username",
                "as": "user_info"
            }},
            {"$project": {
                "username": "$_id",
                "total_annotations": 1,
                "unique_ne_count": {"$size": "$unique_ne_types"},
                "unique_phrases_count": {"$size": "$unique_phrases"},
                "project_count": {"$size": {
                    "$setUnion": [
                        {"$map": {
                            "input": "$projects",
                            "as": "project",
                            "in": {
                                "$arrayElemAt": [
                                    {"$split": ["$$project", "_"]},
                                    0
                                ]
                            }
                        }}
                    ]
                }},
                "first_annotation": 1,
                "last_annotation": 1,
                "activity_days": {
                    "$cond": [
                        {"$and": ["$first_annotation", "$last_annotation"]},
                        {"$divide": [
                            {"$subtract": ["$last_annotation", "$first_annotation"]},
                            1000 * 60 * 60 * 24
                        ]},
                        0
                    ]
                },
                "annotations_per_day": {
                    "$cond": [
                        {"$gt": ["$total_annotations", 0]},
                        {"$divide": [
                            "$total_annotations",
                            {"$max": [{"$add": ["$daily_verage", 1]}, 1]}
                        ]},
                        0
                    ]
                },
                "full_name": {"$arrayElemAt": ["$user_info.full_name", 0]},
                "organization": {"$arrayElemAt": ["$user_info.organization", 0]},
                "role": {"$arrayElemAt": ["$user_info.role", 0]},
                "_id": 0
            }},
            {"$sort": {"total_annotations": -1}}
        ]))
        
        # Enhanced project progress analytics
        project_progress = list(projects_collection.aggregate([
            {"$lookup": {
                "from": "sentences",
                "localField": "_id",
                "foreignField": "project_id",
                "as": "project_sentences"
            }},
            {"$unwind": "$project_sentences"},
            {"$group": {
                "_id": {
                    "project_id": "$_id",
                    "project_name": "$name",
                    "language": "$language"
                },
                "total_sentences": {"$sum": 1},
                "annotated_sentences": {"$sum": {"$cond": ["$project_sentences.is_annotated", 1, 0]}},
                "assigned_users": {"$addToSet": "$project_sentences.username"},
                "total_annotations": {
                    "$sum": {
                        "$size": {
                            "$ifNull": ["$project_sentences.annotation_tags", []]
                        }
                    }
                }
            }},
            {"$lookup": {
                "from": "tags",
                "let": {"project_id": "$_id.project_id"},
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$in": ["$source_sentence_id", {
                                "$map": {
                                    "input": "$project_sentences",
                                    "as": "sentence",
                                    "in": {"$toString": "$$sentence._id"}
                                }
                            }]
                        }
                    }},
                    {"$group": {
                        "_id": None,
                        "project_tags": {"$sum": 1}
                    }}
                ],
                "as": "tag_info"
            }},
            {"$project": {
                "project_name": "$_id.project_name",
                "language": "$_id.language",
                "total_sentences": 1,
                "annotated_sentences": 1,
                "completion_rate": {
                    "$multiply": [
                        {"$divide": ["$annotated_sentences", "$total_sentences"]},
                        100
                    ]
                },
                "assigned_users_count": {"$size": "$assigned_users"},
                "total_annotations": {"$arrayElemAt": ["$tag_info.project_tags", 0]},
                "annotation_density": {
                    "$divide": [
                        {"$arrayElemAt": ["$tag_info.project_tags", 0]},
                        "$total_sentences"
                    ]
                },
                "status": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$annotated_sentences", 0]}, "then": "Not Started"},
                            {"case": {"$eq": ["$annotated_sentences", "$total_sentences"]}, "then": "Completed"},
                            {"case": {"$gt": ["$annotated_sentences", 0]}, "then": "In Progress"}
                        ],
                        "default": "Unknown"
                    }
                }
            }},
            {"$sort": {"completion_rate": -1}}
        ]))
        
        # Enhanced timeline analytics with moving average and trends
        timeline_data = list(tags_collection.aggregate([
            {"$match": tag_filter},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$annotation_date"
                    }
                },
                "daily_annotations": {"$sum": 1},
                "unique_annotators": {"$addToSet": "$username"},
                "ne_types_used": {"$addToSet": "$tag"}
            }},
            {"$sort": {"_id": 1}},
            {"$project": {
                "date": "$_id",
                "daily_annotations": 1,
                "unique_annotators_count": {"$size": "$unique_annotators"},
                "ne_types_count": {"$size": "$ne_types_used"},
                "avg_annotations_per_user": {
                    "$divide": ["$daily_annotations", {"$max": [{"$size": "$unique_annotators"}, 1]}]
                },
                "_id": 0
            }}
        ]))
        
        # Calculate 7-day moving average and trends
        for i in range(6, len(timeline_data)):
            window = timeline_data[i-6:i+1]
            moving_avg = sum(item['daily_annotations'] for item in window) / 7
            timeline_data[i]['moving_average_7d'] = round(moving_avg, 2)
        
        # Calculate overall trends
        if len(timeline_data) >= 7:
            first_week_avg = sum(item['daily_annotations'] for item in timeline_data[:7]) / 7
            last_week_avg = sum(item['daily_annotations'] for item in timeline_data[-7:]) / 7
            growth_rate = ((last_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg > 0 else 0
        else:
            growth_rate = 0
        
        # Enhanced NE type distribution with trends
        ne_distribution = list(tags_collection.aggregate([
            {"$match": tag_filter},
            {"$group": {
                "_id": "$tag",
                "count": {"$sum": 1},
                "unique_phrases": {"$addToSet": "$text"},
                "unique_users": {"$addToSet": "$username"},
                "first_use": {"$min": "$annotation_date"},
                "last_use": {"$max": "$annotation_date"},
                "projects": {"$addToSet": "$source_sentence_id"}
            }},
            {"$project": {
                "ne_type": "$_id",
                "count": 1,
                "unique_phrases_count": {"$size": "$unique_phrases"},
                "unique_users_count": {"$size": "$unique_users"},
                "project_count": {"$size": {
                    "$setUnion": [
                        {"$map": {
                            "input": "$projects",
                            "as": "project",
                            "in": {
                                "$arrayElemAt": [
                                    {"$split": ["$$project", "_"]},
                                    0
                                ]
                            }
                        }}
                    ]
                }},
                "popularity_score": {
                    "$multiply": [
                        {"$divide": ["$count", total_annotations]},
                        100
                    ]
                },
                "adoption_rate": {
                    "$divide": ["$unique_users_count", {"$size": {"$ifNull": [user_performance, []]}}]
                },
                "first_use": 1,
                "last_use": 1,
                "usage_trend": {
                    "$cond": [
                        {"$and": ["$first_use", "$last_use"]},
                        {"$divide": [
                            "$count",
                            {"$max": [{
                                "$divide": [
                                    {"$subtract": ["$last_use", "$first_use"]},
                                    1000 * 60 * 60 * 24
                                ]
                            }, 1]}
                        ]},
                        0
                    ]
                }
            }},
            {"$sort": {"count": -1}}
        ]))
        
        # Enhanced quality metrics
        quality_metrics = {
            "average_annotations_per_user": total_annotations / max(len(user_performance), 1),
            "top_performer": user_performance[0] if user_performance else None,
            "most_common_ne": ne_distribution[0] if ne_distribution else None,
            "total_projects": len(project_progress),
            "active_projects": len([p for p in project_progress if p.get('completion_rate', 0) < 100 and p.get('completion_rate', 0) > 0]),
            "completed_projects": len([p for p in project_progress if p.get('completion_rate', 0) == 100]),
            "annotation_growth_rate": round(growth_rate, 2),
            "overall_annotation_quality": "High" if total_annotations > 1000 else "Medium" if total_annotations > 500 else "Low",
            "user_engagement_score": len([u for u in user_performance if u.get('total_annotations', 0) > 10]) / max(len(user_performance), 1) * 100
        }
        
        # Executive summary for different report levels
        executive_summary = {
            "standard": {
                "total_annotations": total_annotations,
                "active_users": len(user_performance),
                "project_completion": f"{len([p for p in project_progress if p.get('completion_rate', 0) == 100])}/{len(project_progress)}",
                "avg_daily_annotations": sum(item['daily_annotations'] for item in timeline_data) / max(len(timeline_data), 1) if timeline_data else 0
            },
            "detailed": {
                **quality_metrics,
                "ne_diversity": len(ne_distribution),
                "avg_project_completion": sum(p.get('completion_rate', 0) for p in project_progress) / max(len(project_progress), 1),
                "annotation_consistency": "High" if len(set(ne.get('ne_type') for mwe in ne_distribution)) > 10 else "Medium"
            },
            "executive": {
                "performance_rating": "Excellent" if quality_metrics['user_engagement_score'] > 80 else "Good" if quality_metrics['user_engagement_score'] > 60 else "Needs Improvement",
                "key_achievements": [
                    f"{quality_metrics['completed_projects']} projects completed",
                    f"{total_annotations} total annotations",
                    f"{len(ne_distribution)} NE types identified"
                ],
                "recommendations": [
                    "Increase user training on rare NE types" if any(ne.get('unique_users_count', 0) < 3 for ne in ne_distribution) else "Maintain current annotation quality",
                    "Focus on incomplete projects" if quality_metrics['active_projects'] > 2 else "All projects are on track"
                ]
            }
        }
        
        return jsonify({
            "report_metadata": {
                "generated_at": get_ist_time().isoformat(),
                "report_level": report_level,
                "filters_applied": {
                    "language": language,
                    "project_id": project_id,
                    "username": username,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "data_freshness": "Real-time"
            },
            "executive_summary": executive_summary.get(report_level, executive_summary["standard"]),
            "user_performance": user_performance,
            "project_progress": project_progress,
            "timeline_data": timeline_data,
            "ne_distribution": ne_distribution,
            "quality_metrics": quality_metrics,
            "key_insights": {
                "busiest_day": max(timeline_data, key=lambda x: x['daily_annotations']) if timeline_data else None,
                "most_productive_user": max(user_performance, key=lambda x: x['total_annotations']) if user_performance else None,
                "most_diverse_annotator": max(user_performance, key=lambda x: x['unique_ne_count']) if user_performance else None,
                "most_complex_project": max(project_progress, key=lambda x: x.get('total_annotations', 0)) if project_progress else None
            }
        }), 200
        
    except Exception as e:
        print(f"Error generating enhanced comprehensive report: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
# --- Recommendation Endpoints  ---
@app.route("/api/recommend-tags", methods=["POST"])
def recommend_tags():
    """
    Recommends tags for phrases in a file based on previously annotated data.
    Compares phrases in the uploaded file against existing annotations in the database.
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Extract text from the uploaded file
        file_extension = os.path.splitext(file.filename)[1].lower()
        sentences_data = extract_text_from_file(file, file_extension)
        
        if not sentences_data:
            return jsonify({"error": "No valid sentences found in the file"}), 400
        
        # Get all existing tags from the database to build recommendation database
        all_tags = list(tags_collection.find({}, {
            "text": 1, 
            "tag": 1,
            "annotation_date": 1
        }))
        
        # Build a dictionary of phrase -> tag mappings with confidence scores
        phrase_tag_mappings = {}
        
        for tag in all_tags:
            phrase = tag.get('text', '').strip().lower()
            tag_type = tag.get('tag', '')
            
            if phrase and tag_type:
                if phrase not in phrase_tag_mappings:
                    phrase_tag_mappings[phrase] = {}
                
                if tag_type not in phrase_tag_mappings[phrase]:
                    phrase_tag_mappings[phrase][tag_type] = 0
                
                phrase_tag_mappings[phrase][tag_type] += 1
        
        # Process each sentence to find recommendations
        recommendations = []
        
        for sentence_data in sentences_data:
            sentence_text = sentence_data.get('textContent', '').strip().lower()
            sentence_recommendations = []
            
            # Check each known phrase against the sentence
            for phrase, tag_counts in phrase_tag_mappings.items():
                if phrase and phrase in sentence_text:
                    # Find the most frequent tag for this phrase
                    most_common_tag = max(tag_counts.items(), key=lambda x: x[1])
                    
                    recommendation = {
                        "phrase": phrase,
                        "recommended_tag": most_common_tag[0],
                        "confidence": min(most_common_tag[1] / 10.0, 1.0),  # Normalize confidence (max 1.0)
                        "occurrence_count": most_common_tag[1],
                        "sentence_context": sentence_text
                    }
                    sentence_recommendations.append(recommendation)
            
            # Sort recommendations by confidence (highest first)
            sentence_recommendations.sort(key=lambda x: x['confidence'], reverse=True)
            
            if sentence_recommendations:
                recommendations.append({
                    "sentence": sentence_text,
                    "recommendations": sentence_recommendations[:5]  # Top 5 recommendations per sentence
                })
        
        return jsonify({
            "total_sentences_processed": len(sentences_data),
            "sentences_with_recommendations": len(recommendations),
            "recommendations": recommendations,
            "phrase_database_size": len(phrase_tag_mappings)
        }), 200
        
    except Exception as e:
        print(f"Error generating tag recommendations: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/api/analytics/reviewer-stats", methods=["GET"])
@token_required
def get_reviewer_stats():
    """Get reviewer-specific statistics - ENHANCED VERSION"""
    try:
        current_user = request.current_user
        reviewer_username = current_user.get('username')
        
        print(f"DEBUG: Fetching stats for reviewer: {reviewer_username}")
        
        # Count total projects with annotated sentences
        total_projects = projects_collection.count_documents({})
        
        # FIXED: Count sentences reviewed by this reviewer
        total_sentences_reviewed = sentences_collection.count_documents({
            "$or": [
                {"reviewed_by": reviewer_username},
                {"review_status": {"$in": ["Approved", "Rejected", "Partially Approved"]}}
            ]
        })
        
        # FIXED: Count pending reviews (annotated but not reviewed)
        pending_sentences = sentences_collection.count_documents({
            "is_annotated": True,
            "$or": [
                {"review_status": {"$in": [None, "Pending"]}},
                {"review_status": {"$exists": False}}
            ]
        })
        
        # FIXED: Calculate review accuracy
        approved_count = sentences_collection.count_documents({
            "review_status": "Approved"
        })
        
        rejected_count = sentences_collection.count_documents({
            "review_status": "Rejected"
        })
        
        total_reviewed = approved_count + rejected_count
        review_accuracy = (approved_count / total_reviewed * 100) if total_reviewed > 0 else 0
        
        print(f"DEBUG: Stats - projects: {total_projects}, reviewed: {total_sentences_reviewed}, pending: {pending_sentences}, accuracy: {review_accuracy}%")
        
        return jsonify({
            "totalProjects": total_projects,
            "totalSentencesReviewed": total_sentences_reviewed,
            "pendingReviews": pending_sentences,
            "reviewAccuracy": round(review_accuracy, 1)
        }), 200
        
    except Exception as e:
        print(f"Error fetching reviewer stats: {e}")
        return jsonify({
            "totalProjects": 0,
            "totalSentencesReviewed": 0, 
            "pendingReviews": 0,
            "reviewAccuracy": 0
        }), 200
                   
@app.route("/api/recommend-tags/text", methods=["POST"])
def recommend_tags_from_text():
    """
    Recommends tags for a specific text input (for real-time suggestions during annotation).
    """
    try:
        data = request.json
        text_content = data.get('text', '').strip().lower()
        
        if not text_content:
            return jsonify({"error": "Text content is required"}), 400
        
        # Get all existing tags from the database
        all_tags = list(tags_collection.find({}, {
            "text": 1, 
            "tag": 1,
            "annotation_date": 1,
            "username": 1
        }))
        
        # Build phrase mappings
        phrase_tag_mappings = {}
        phrase_details = {}
        
        for tag in all_tags:
            phrase = tag.get('text', '').strip().lower()
            tag_type = tag.get('tag', '')
            
            if phrase and tag_type:
                if phrase not in phrase_tag_mappings:
                    phrase_tag_mappings[phrase] = {}
                    phrase_details[phrase] = {
                        "examples": [],
                        "annotators": set(),
                        "first_seen": tag.get('annotation_date'),
                        "last_seen": tag.get('annotation_date')
                    }
                
                if tag_type not in phrase_tag_mappings[phrase]:
                    phrase_tag_mappings[phrase][tag_type] = 0
                
                phrase_tag_mappings[phrase][tag_type] += 1
                phrase_details[phrase]["annotators"].add(tag.get('username', 'unknown'))
                
                # Update timestamps
                if tag.get('annotation_date'):
                    if (phrase_details[phrase]["first_seen"] is None or 
                        tag['annotation_date'] < phrase_details[phrase]["first_seen"]):
                        phrase_details[phrase]["first_seen"] = tag['annotation_date']
                    
                    if (phrase_details[phrase]["last_seen"] is None or 
                        tag['annotation_date'] > phrase_details[phrase]["last_seen"]):
                        phrase_details[phrase]["last_seen"] = tag['annotation_date']
        
        # Find matching phrases in the input text
        recommendations = []
        
        for phrase, tag_counts in phrase_tag_mappings.items():
            if phrase and phrase in text_content:
                # Calculate position in text
                start_pos = text_content.find(phrase)
                end_pos = start_pos + len(phrase)
                
                # Get the most common tag
                most_common_tag = max(tag_counts.items(), key=lambda x: x[1])
                total_occurrences = sum(tag_counts.values())
                
                recommendation = {
                    "phrase": phrase,
                    "recommended_tag": most_common_tag[0],
                    "confidence": min(most_common_tag[1] / max(total_occurrences, 10), 1.0),
                    "occurrence_count": most_common_tag[1],
                    "total_occurrences": total_occurrences,
                    "position_in_text": {
                        "start": start_pos,
                        "end": end_pos
                    },
                    "coverage": {
                        "total_annotators": len(phrase_details[phrase]["annotators"]),
                        "first_seen": phrase_details[phrase]["first_seen"].isoformat() if phrase_details[phrase]["first_seen"] else None,
                        "last_seen": phrase_details[phrase]["last_seen"].isoformat() if phrase_details[phrase]["last_seen"] else None
                    },
                    "alternative_tags": [
                        {"tag": tag, "count": count} 
                        for tag, count in tag_counts.items() 
                        if tag != most_common_tag[0]
                    ]
                }
                recommendations.append(recommendation)
        
        # Sort by confidence and then by occurrence count
        recommendations.sort(key=lambda x: (x['confidence'], x['occurrence_count']), reverse=True)
        
        return jsonify({
            "input_text": text_content,
            "recommendations": recommendations[:10],  # Top 10 recommendations
            "total_matches_found": len(recommendations)
        }), 200
        
    except Exception as e:
        print(f"Error generating text tag recommendations: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500





@app.route("/api/recommendation-stats", methods=["GET"])
def get_recommendation_stats():
    """
    Get statistics about the tag recommendation database.
    """
    try:
        # Count total annotated phrases
        total_phrases = tags_collection.distinct("text")
        
        # Count by tag type
        pipeline = [
            {"$group": {
                "_id": "$tag",
                "count": {"$sum": 1},
                "unique_phrases": {"$addToSet": "$text"}
            }},
            {"$project": {
                "tag_type": "$_id",
                "total_annotations": "$count",
                "unique_phrases_count": {"$size": "$unique_phrases"},
                "_id": 0
            }}
        ]
        
        tag_stats = list(tags_collection.aggregate(pipeline))
        
        # Get most common phrases
        common_phrases_pipeline = [
            {"$group": {
                "_id": "$text",
                "occurrence_count": {"$sum": 1},
                "different_tags": {"$addToSet": "$tag"}
            }},
            {"$project": {
                "phrase": "$_id",
                "occurrence_count": 1,
                "tag_variety_count": {"$size": "$different_tags"},
                "_id": 0
            }},
            {"$sort": {"occurrence_count": -1}},
            {"$limit": 20}
        ]
        
        common_phrases = list(tags_collection.aggregate(common_phrases_pipeline))
        
        return jsonify({
            "total_annotated_phrases": len(total_phrases),
            "tag_statistics": tag_stats,
            "most_common_phrases": common_phrases
        }), 200
        
    except Exception as e:
        print(f"Error fetching recommendation stats: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/debug-sentence/<sentence_id>", methods=["GET"])
def debug_sentence(sentence_id):
    """Debug endpoint to check sentence and tag data"""
    try:
        sentence = sentences_collection.find_one({"_id": ObjectId(sentence_id)})
        if not sentence:
            return jsonify({"error": "Sentence not found"}), 404
        
        # Check tags in both collections
        final_tags = list(tags_collection.find({"source_sentence_id": sentence_id}))
        staged_tags = list(staged_tags_collection.find({"source_sentence_id": sentence_id}))
        
        return jsonify({
            "sentence": {
                "_id": str(sentence["_id"]),
                "textContent": sentence.get("textContent"),
                "is_annotated": sentence.get("is_annotated", False),
                "project_id": sentence.get("project_id"),
                "username": sentence.get("username")
            },
            "final_tags": [{
                "_id": str(tag["_id"]),
                "text": tag.get("text"),
                "tag": tag.get("tag"),
                "username": tag.get("username")
            } for tag in final_tags],
            "staged_tags": [{
                "_id": str(tag["_id"]),
                "text": tag.get("text"),
                "tag": tag.get("tag"), 
                "username": tag.get("username")
            } for tag in staged_tags],
            "total_tags": len(final_tags) + len(staged_tags)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Project Management Endpoints (UNCHANGED) ---

@app.route("/api/projects", methods=["POST"])
@admin_required
def create_project():
    try:
        file = request.files.get('file')
        project_name = request.form.get('projectName')
        project_description = request.form.get('projectDescription')
        language = request.form.get('language')
        assigned_user = request.form.get('assignedUser')
        sentence_range = request.form.get('sentenceRange') 
        admin_username = request.form.get('adminUsername')

        if not project_name or not assigned_user or not admin_username:
            return jsonify({"error": "Missing project name, assigned user, or admin username."}), 400

        is_file_upload = file is not None and file.filename != ''
        
        if not is_file_upload:
            return jsonify({"error": "Missing file. Please upload a sentence file."}), 400

        # Extract sentences and metadata from file
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.txt', '.pdf', '.doc', '.docx', '.csv', '.xml']:
            return jsonify({"error": "Unsupported file type. Use TXT, PDF, DOC/DOCX, CSV, or XML."}), 400
        
        all_sentences_data = extract_text_from_file(file, file_extension)
        
        if not all_sentences_data:
            return jsonify({"error": "No valid sentences found in the file"}), 400
        
        project_tasks_data = all_sentences_data
        IST = ZoneInfo("Asia/Kolkata")
        
        # Create project document
        project_doc = projects_collection.insert_one({
            "name": project_name,
            "description": project_description or "",
            "language": language or "Unknown",
            "total_sentences": len(project_tasks_data),
            "file_name": file.filename if is_file_upload else None,
            "uploaded_by": admin_username,
            "created_at": datetime.now(IST) 
        })
        project_id = str(project_doc.inserted_id)

        # Insert tasks (sentences) and corresponding tags
        tags_to_insert = []
        
        for index, task_data in enumerate(project_tasks_data):
            sentence_text = task_data['textContent'].strip()
            
            if sentence_text:
                new_sentence_doc = {
                    "username": assigned_user,
                    "textContent": sentence_text,
                    "is_annotated": task_data.get('is_annotated', False),
                    "annotation_tags": [], 
                    "annotation_email": None,
                    "annotation_datetime": None,
                    "project_id": project_id, 
                    "original_index": index 
                }

                inserted_sentence_result = sentences_collection.insert_one(new_sentence_doc)
                new_sentence_id = str(inserted_sentence_result.inserted_id)
                
                # If the task came pre-annotated, insert the tags directly into tags_collection
                if task_data.get('is_annotated', False) and task_data.get('tags'):
                    for tag in task_data['tags']:
                        # PRESERVE original annotation metadata
                        annotated_by_user = tag.get('annotated_by', assigned_user)
                        
                        # Try to use the original annotation date, fallback to current time
                        original_date = get_ist_time()
                        if tag.get('annotated_on'):
                            try:
                                # Parse the date from XML (format: YYYY-MM-DD)
                                original_date = datetime.strptime(tag['annotated_on'], '%Y-%m-%d')
                            except:
                                original_date = get_ist_time()
                        
                        # Create tag document for direct insertion into tags_collection
                        tag_doc = {
                            "username": annotated_by_user,
                            "text": tag.get('text', sentence_text),
                            "tag": tag.get('tag', 'Concept'),
                            "source_sentence_id": new_sentence_id,
                            "annotation_date": original_date,
                            "review_status": "Approved",  # Directly approve imported tags
                            "reviewed_by": "system_import",
                            "reviewed_at": get_ist_time()
                        }
                        tags_to_insert.append(tag_doc)

        # Insert all tags directly into tags_collection (not staged_tags_collection)
        if tags_to_insert:
            tags_collection.insert_many(tags_to_insert)
            # Also insert into search_tags_collection for search functionality
            search_tags_collection.insert_many(tags_to_insert)
            print(f"DEBUG: Inserted {len(tags_to_insert)} pre-annotated tags directly into tags_collection")

        log_action_and_update_report(admin_username, f'Created project "{project_name}" and assigned {len(project_tasks_data)} sentences to {assigned_user}')
        return jsonify({"message": f"Project '{project_name}' created and {len(project_tasks_data)} sentences assigned to {assigned_user}. {len(tags_to_insert)} pre-annotated tags imported."}), 201

    except ValueError as ve:
        return jsonify({"error": f"File parsing error: {str(ve)}"}), 400
    except Exception as e:
        print(f"Error creating project: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/api/projects/standalone", methods=["POST"])
def create_project_standalone_flask():
    """
    Creates a new Project using raw data (not file upload), and parses it 
    with the detailed XML and plain-text logic (standard English splitting).
    """
    data = request.json
    current_user = data.get('uploaded_by', 'system_user') # Assuming this comes from the request data now

    print("Creating Project (Standalone Logic)...")

    # 1. Create and add the new Project record
    project_doc = projects_collection.insert_one({
        "name": data.get('title', 'Untitled Project'),
        "description": data.get('description', ''),
        "language": data.get('language', 'Unknown'),
        "file_text": data.get('file_text', ''),
        "uploaded_by": current_user,
        "created_at": get_ist_time(),
        "total_sentences": 0 # Will be updated later if sentences are found
    })
    new_project_id = str(project_doc.inserted_id)
    
    file_text = data.get('file_text', '').strip()
    is_xml = file_text.startswith("<") and file_text.endswith(">")
    sentence_counter = 1
    tags_to_insert = []
    
    # --- XML Processing Block ---
    if is_xml:
        print("Detected XML input.") 
        try:
            # Note: Using xml.etree.ElementTree (ET) as in the original standalone function
            root = ET.fromstring(file_text) 
            print("XML Parsed Successfully.") 

            decoded_text = html.unescape(file_text)
            # Check for inline annotations (OLD format)
            contains_inline_annotations = re.search(r'<(TIMEX|NUMEX)', decoded_text) is not None

            # --- OLD XML Format (Inline Annotations) ---
            if contains_inline_annotations:
                print("Detected inline annotations. Processing OLD XML format.")
                for sentence_elem in root.findall(".//sentence"):
                    raw_text = sentence_elem.get("text", "").strip()
                    is_annotated = sentence_elem.get("isAnnotated") == "True"
                    annotations = []

                    def annotation_extractor(match):
                        annotation_type = match.group(1)
                        attributes = match.group(2)
                        annotated_word = html.unescape(match.group(3))

                        annotation_attrs = dict(re.findall(r'(\w+)="(.*?)"', attributes))
                        annotations.append({
                            'type': annotation_type,
                            'text': annotated_word,
                            'attributes': annotation_attrs
                        })
                        return annotated_word

                    # Remove inline annotation tags and extract data
                    clean_text = re.sub(r'<(\w+)(.*?)>(.*?)</\1>', annotation_extractor, decoded_text)
                    
                    if clean_text:
                        # Save the Sentence record
                        new_sentence_doc = {
                            "username": current_user, # Assign to the user who uploaded the data
                            "textContent": clean_text,
                            "is_annotated": is_annotated,
                            "annotation_email": data.get('email'),
                            "annotation_datetime": get_ist_time() if is_annotated else None,
                            "project_id": new_project_id, 
                            "original_index": sentence_counter 
                        }
                        inserted_sentence_result = sentences_collection.insert_one(new_sentence_doc)
                        new_sentence_id = str(inserted_sentence_result.inserted_id)

                        # Save the Annotation records
                        if is_annotated:
                            for annotation in annotations:
                                annotation_type = annotation['type']
                                annotation_subtype = annotation['attributes'].get('TYPE', '')
                                annotated_word = annotation['text']
                                
                                tags_to_insert.append({
                                    "username": current_user,
                                    "text": annotated_word,
                                    "tag": f"{annotation_type} ({annotation_subtype})",
                                    "source_sentence_id": new_sentence_id,
                                    "annotation_date": get_ist_time()
                                })

                        sentence_counter += 1

            # --- NEW XML Format (Nested Annotations) ---
            else:
                print("Processing NEW Annotated XML format.") 
                sentences_root = root.find("./sentences")
                if sentences_root is None:
                    raise ValueError("Invalid XML: <sentences> tag missing inside <project>.")
                
                for sentence_elem in sentences_root.findall(".//sentence"):
                    raw_text = sentence_elem.get("text", "").strip()
                    is_annotated = sentence_elem.get("isAnnotated") == "True"
                    
                    if raw_text:
                        new_sentence_doc = {
                            "username": current_user,
                            "textContent": raw_text,
                            "is_annotated": is_annotated,
                            "annotation_email": data.get('email'),
                            "annotation_datetime": get_ist_time() if is_annotated else None,
                            "project_id": new_project_id,
                            "original_index": sentence_counter
                        }
                        inserted_sentence_result = sentences_collection.insert_one(new_sentence_doc)
                        new_sentence_id = str(inserted_sentence_result.inserted_id)

                        annotations_elem = sentence_elem.find("annotations")
                        if annotations_elem is not None:
                            for annotation_elem in annotations_elem.findall("annotation"):
                                annotated_word = annotation_elem.get("word_phrase")
                                annotation_type = annotation_elem.get("annotation")
                                annotated_by_xml = annotation_elem.get("annotated_by")
                                annotated_on_str = annotation_elem.get("annotated_on")
                                
                                # Convert date string to datetime object
                                try:
                                    annotated_on_dt = datetime.strptime(annotated_on_str, "%Y-%m-%d")
                                except:
                                    annotated_on_dt = get_ist_time()

                                tags_to_insert.append({
                                    "username": current_user, 
                                    "text": annotated_word,
                                    "tag": annotation_type,
                                    "source_sentence_id": new_sentence_id,
                                    "annotation_date": annotated_on_dt
                                })
                        
                        sentence_counter += 1

        except ET.ParseError as e:
            # Need to manually clean up the created project document
            projects_collection.delete_one({"_id": ObjectId(new_project_id)})
            return jsonify({'message': f'Invalid XML format: {str(e)}'}), 400
        except Exception as e:
            projects_collection.delete_one({"_id": ObjectId(new_project_id)})
            return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500
    
    # --- Plain Text Processing Block (Standard Punctuation Split) ---
    else:
        print("Detected Plain Text input.")

        # Standard sentence splitting for English
        sentences = re.split(r'[।|॥|\.|\?|!]\s*', file_text)

        for sentence_text in sentences:
            clean_text = sentence_text.strip()
            if clean_text:
                new_sentence_doc = {
                    "username": current_user,
                    "textContent": clean_text,
                    "is_annotated": False,
                    "annotation_email": None,
                    "annotation_datetime": None,
                    "project_id": new_project_id,
                    "original_index": sentence_counter
                }
                sentences_collection.insert_one(new_sentence_doc)
                sentence_counter += 1
    
    # Final steps (Bulk insert tags and update project count)
    if tags_to_insert:
        tags_collection.insert_many(tags_to_insert)
        search_tags_collection.insert_many(tags_to_insert)

    projects_collection.update_one(
        {"_id": ObjectId(new_project_id)},
        {"$set": {"total_sentences": sentence_counter - 1}}
    )

    print("Project Successfully Created!") 
    return jsonify({"message": f"Project created successfully with {sentence_counter - 1} sentences."}), 201



@app.route("/api/projects", methods=["GET"])
def get_projects():
    """
    FIXED: Correctly handles project ID matching between projects and sentences
    """
    try:
        # Step 1: Get all project metadata and convert _id to string for matching
        projects_cursor = projects_collection.find({}, {
            "name": 1,
            "description": 1,
            "language": 1,
            "created_at": 1
        }).sort("created_at", -1)
        
        # Create a mapping of string project IDs to project data
        projects_map = {}
        for p in projects_cursor:
            project_id_str = str(p["_id"])
            projects_map[project_id_str] = p
        
        project_ids = list(projects_map.keys())
        
        if not project_ids:
            return jsonify([]), 200

        # Step 2: Aggregation Pipeline - match using string project IDs
        pipeline = [
            # Match only sentences belonging to the active projects
            {"$match": {"project_id": {"$in": project_ids}}},
            
            # Group by project_id AND original_index to get unique sentences
            {"$group": {
                "_id": {
                    "project_id": "$project_id",
                    "original_index": "$original_index"
                },
                # For each unique sentence, check if ANY copy is annotated
                "is_annotated_any": {"$max": {"$cond": ["$is_annotated", 1, 0]}},
                "project_id": {"$first": "$project_id"}
            }},
            
            # Now group by project_id to get final counts
            {"$group": {
                "_id": "$project_id",
                "total_sentences": {"$sum": 1},
                "annotated_count": {"$sum": "$is_annotated_any"}
            }},
            
            # Add fields to structure the output
            {"$addFields": {
                "project_id": "$_id"
            }}
        ]
        
        # Execute the aggregation
        stats_results = {item['project_id']: item for item in sentences_collection.aggregate(pipeline)}
        
        projects_list = []
        
        # Step 3: Combine metadata with calculated statistics
        for project_id_str, project in projects_map.items():
            stats = stats_results.get(project_id_str, {})
            total_sentences = stats.get("total_sentences", 0)
            annotated_count = stats.get("annotated_count", 0)
            
            progress_percent = math.ceil((annotated_count / total_sentences) * 100) if total_sentences > 0 else 0
            
            # Get assigned users for this project
            assigned_users = sentences_collection.distinct("username", {"project_id": project_id_str})
            
            projects_list.append({
                "id": project_id_str,
                "name": project["name"],
                "description": project.get("description", "No description provided."),
                "language": project.get("language", "N/A"),
                "assigned_users_count": len(assigned_users),
                "total_sentences": total_sentences,
                "annotated_count": annotated_count,
                "not_annotated_count": total_sentences - annotated_count, 
                "progress_percent": progress_percent,
                "assigned_user": assigned_users[0] if assigned_users else 'N/A',  # Show first user as primary
                "assigned_users": assigned_users,  # Include all assigned users
                "done": annotated_count,  # For the project card display (e.g., "2/72")
                "total": total_sentences   # For the project card display
            })
            
        return jsonify(projects_list), 200
        
    except Exception as e:
        print(f"Error fetching projects (CORRECTED): {e}")
        return jsonify({"error": "Internal server error during project fetch"}), 500
    
   
@app.route("/api/projects/<project_id>/assign_user", methods=["POST"])
def assign_user_to_project(project_id):
    data = request.json
    new_users = data.get("users", [])
    admin_username = data.get("adminUsername")

    if not new_users:
        return jsonify({"error": "No users selected for assignment."}), 400

    project = projects_collection.find_one({"_id": ObjectId(project_id)})
    if not project:
        return jsonify({"error": "Project not found"}), 404

    try:
        # 1. Find the existing set of unique tasks and their annotation status from the current pool.
        # This ensures consistency across assignments.
        unique_tasks_cursor = sentences_collection.find({
            "project_id": project_id
        }, {
            "textContent": 1, 
            "original_index": 1,
            "is_annotated": 1, 
            "_id": 1 
        })

        tasks_pool = {}
        for task in unique_tasks_cursor:
            idx = task['original_index']
            
            # Consolidate status: Prioritize 'annotated' status if multiple copies exist for the same task index
            if idx not in tasks_pool or task.get('is_annotated'):
                tasks_pool[idx] = {
                    "textContent": task["textContent"],
                    "original_index": idx,
                    "is_annotated_in_pool": task.get('is_annotated', False),
                    "original_sentence_id": str(task['_id']) if task.get('is_annotated') else None
                }
        
        tasks_to_assign = list(tasks_pool.values())
        
        if not tasks_to_assign:
            return jsonify({"message": f"Project '{project['name']}' has no sentences to assign."}), 200

        # 2. Map tags from the original annotated sentences for duplication
        tag_map = {}
        annotated_task_ids = [t['original_sentence_id'] for t in tasks_to_assign if t['is_annotated_in_pool'] and t['original_sentence_id'] is not None]
        
        if annotated_task_ids:
            for tag in tags_collection.find({"source_sentence_id": {"$in": annotated_task_ids}}):
                old_sentence_id = tag['source_sentence_id']
                if old_sentence_id not in tag_map:
                    tag_map[old_sentence_id] = []
                
                # Prepare the tag document for duplication (remove _id and username)
                new_tag = {k: v for k, v in tag.items() if k not in ['_id', 'source_sentence_id', 'username']}
                tag_map[old_sentence_id].append(new_tag)


        inserted_count = 0
        tags_to_insert = []
        
        for user_to_assign in new_users:
            for task in tasks_to_assign:
                
                # Check if this specific task is already assigned to the user
                exists = sentences_collection.find_one({
                    "project_id": project_id,
                    "username": user_to_assign,
                    "original_index": task["original_index"]
                })
                
                if not exists:
                    is_annotated_for_new_user = task['is_annotated_in_pool']

                    # Insert the new sentence document to get the new MongoDB ID
                    new_sentence_template = {
                        "username": user_to_assign,
                        "textContent": task["textContent"],
                        "is_annotated": is_annotated_for_new_user, 
                        "annotation_tags": [], 
                        "annotation_email": None,
                        "annotation_datetime": None,
                        "project_id": project_id,
                        "original_index": task["original_index"]
                    }
                    
                    inserted_sentence_doc = sentences_collection.insert_one(new_sentence_template)
                    new_sentence_id = str(inserted_sentence_doc.inserted_id)
                    inserted_count += 1
                    
                    # If the original task was annotated, duplicate the tags
                    if is_annotated_for_new_user and task.get('original_sentence_id'):
                        old_sentence_id = task['original_sentence_id']
                        
                        if old_sentence_id in tag_map:
                            for tag_template in tag_map[old_sentence_id]:
                                # Duplicate tag and link it to the new sentence ID and new username
                                tags_to_insert.append({
                                    **tag_template,
                                    'source_sentence_id': new_sentence_id,
                                    'username': user_to_assign, # Set the correct NEW username
                                    'annotation_date': get_ist_time()
                                })

        if tags_to_insert:
            # Perform bulk insertion of all new tags after sentence creation
            tags_collection.insert_many(tags_to_insert)
            search_tags_collection.insert_many(tags_to_insert)

        log_action_and_update_report(admin_username, f'Assigned project "{project["name"]}" to {len(new_users)} users. Reflected existing pool progress.')
        return jsonify({"message": f"Successfully assigned {len(new_users)} user(s) with {inserted_count} new tasks and tags."}), 201

    except Exception as e:
        print(f"Error assigning user to project: {e}")
        return jsonify({"error": f"Failed to assign user due to server error: {str(e)}", "message": "Assignment failed to fetch"}), 500


@app.route("/api/projects/<project_id>/download", methods=["GET"])
def download_project_data(project_id):
    file_format = request.args.get("format", "Text")
    report_type = request.args.get("report_type", "annotations")  # annotations, statistics, comprehensive
    include_metadata = request.args.get("include_metadata", "true").lower() == "true"

    try:
        print(f"DEBUG: Enhanced download request - project_id: {project_id}, format: {file_format}, report_type: {report_type}")
        
        # Verify the project exists
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project:
            print(f"DEBUG: Project not found with ID: {project_id}")
            return jsonify({"error": "Project not found."}), 404
        
        print(f"DEBUG: Looking for all sentences in project: {project_id}")
        
        # Enhanced aggregation with more data
        pipeline = [
            {"$match": {"project_id": project_id}},
            {"$group": {
                "_id": {
                    "textContent": "$textContent",
                    "original_index": "$original_index"
                },
                "sentence_data": {"$first": "$$ROOT"},
                "all_annotators": {"$push": "$username"},
                "annotation_status": {"$push": "$is_annotated"}
            }},
            {"$sort": {"_id.original_index": 1}},
            {"$addFields": {
                "sentenceIdString": {"$toString": "$sentence_data._id"},
                "is_annotated_any": {"$anyElementTrue": "$annotation_status"}
            }},
            {"$lookup": {
                "from": "tags",
                "localField": "sentenceIdString",
                "foreignField": "source_sentence_id",
                "as": "annotations"
            }}
        ]
        
        unique_sentences = list(sentences_collection.aggregate(pipeline))
        
        print(f"DEBUG: Found {len(unique_sentences)} unique sentences for enhanced download")

        if not unique_sentences:
            return jsonify({"message": "No sentences found for this project."}), 404

        # Enhanced project statistics
        project_stats = {
            "total_sentences": len(unique_sentences),
            "annotated_sentences": sum(1 for s in unique_sentences if s.get("is_annotated_any", False)),
            "total_annotations": sum(len(s.get("annotations", [])) for s in unique_sentences),
            "unique_annotators": len(set(annotator for s in unique_sentences for annotator in s.get("all_annotators", []))),
            "annotation_coverage": (sum(len(s.get("annotations", [])) for s in unique_sentences) / len(unique_sentences)) if unique_sentences else 0
        }

        # --- Enhanced TXT Export Format ---
        if file_format.upper() == "TEXT":
            output = io.StringIO()
            output_lines = []
            
            IST = ZoneInfo("Asia/Kolkata")
            
            # Enhanced header with project metadata
            if include_metadata:
                output_lines.append(f"PROJECT: {project['name']}")
                output_lines.append(f"DESCRIPTION: {project.get('description', 'No description')}")
                output_lines.append(f"LANGUAGE: {project.get('language', 'Unknown')}")
                output_lines.append(f"TOTAL SENTENCES: {project_stats['total_sentences']}")
                output_lines.append(f"ANNOTATED SENTENCES: {project_stats['annotated_sentences']}")
                output_lines.append(f"TOTAL ANNOTATIONS: {project_stats['total_annotations']}")
                output_lines.append(f"UNIQUE ANNOTATORS: {project_stats['unique_annotators']}")
                output_lines.append(f"ANNOTATION COVERAGE: {project_stats['annotation_coverage']:.2f} annotations per sentence")
                output_lines.append(f"EXPORT DATE: {get_ist_time().strftime('%Y-%m-%d %H:%M:%S UTC')}")
                output_lines.append("="*80)
                output_lines.append("")
            
            if report_type == "statistics": 
                # Statistics-only report
                output_lines.append("PROJECT STATISTICS SUMMARY")
                output_lines.append("")
                output_lines.append(f"Completion Rate: {(project_stats['annotated_sentences']/project_stats['total_sentences']*100):.1f}%")
                output_lines.append(f"Average Annotations per Sentence: {project_stats['annotation_coverage']:.2f}")
                output_lines.append("")
                
                # Annotator statistics
                annotator_stats = {}
                for sentence in unique_sentences:
                    for annotator in sentence.get("all_annotators", []):
                        if annotator not in annotator_stats:
                            annotator_stats[annotator] = {"sentences": 0, "annotations": 0}
                        annotator_stats[annotator]["sentences"] += 1
                    for annotation in sentence.get("annotations", []):
                        annotator = annotation.get("username", "Unknown")
                        if annotator not in annotator_stats:
                            annotator_stats[annotator] = {"sentences": 0, "annotations": 0}
                        annotator_stats[annotator]["annotations"] += 1
                
                output_lines.append("ANNOTATOR CONTRIBUTIONS:")
                for annotator, stats in sorted(annotator_stats.items(), key=lambda x: x[1]["annotations"], reverse=True):
                    output_lines.append(f"  {annotator}: {stats['annotations']} annotations across {stats['sentences']} sentences")
                output_lines.append("")
                
                # NE type statistics
                ne_stats = {}
                for sentence in unique_sentences:
                    for annotation in sentence.get("annotations", []):
                        NE_type = annotation.get("tag", "Unknown")
                        ne_stats[ne_type] = ne_stats.get(ne_type, 0) + 1
                
                output_lines.append("NE TYPE DISTRIBUTION:")
                for ne_type, count in sorted(ne_stats.items(), key=lambda x: x[1], reverse=True):
                    output_lines.append(f"  {ne_type}: {count} occurrences")
                
            else:
                # Full annotation report
                for item in unique_sentences:
                    sentence = item["sentence_data"]
                    is_annotated = item.get("is_annotated_any", False)
                    sentence_id = str(sentence["_id"])
                    
                    # Enhanced sentence header
                    text_content = repr(sentence["textContent"])
                    annotators = ", ".join(set(item.get("all_annotators", [])))
                    
                    output_lines.append(f"Sentence ID: {sentence_id}, Text: {text_content}")
                    output_lines.append(f"Annotators: {annotators}, Annotated: {'Yes' if is_annotated else 'No'}")
                    output_lines.append(f"Original Index: {sentence.get('original_index', 'N/A')}")

                    if is_annotated and report_type != "sentences_only":
                        # Enhanced annotation details
                        for tag_doc in item.get('annotations', []):
                            tag_text = tag_doc.get('text', '').strip()
                            tag_label = tag_doc.get('tag', 'UNKNOWN_TAG')
                            annotated_by = tag_doc.get('username', 'Unknown')
                            
                            # Date Formatting
                            annotation_dt_utc = tag_doc.get("annotation_date", get_ist_time())
                            if isinstance(annotation_dt_utc, str):
                                try:
                                    annotation_dt_utc = datetime.fromisoformat(annotation_dt_utc.replace('Z', '+00:00'))
                                except:
                                    annotation_dt_utc = get_ist_time()
                            
                            if annotation_dt_utc.tzinfo is None:
                                annotation_dt_utc = annotation_dt_utc.replace(tzinfo=ZoneInfo("UTC"))
                                
                            annotation_dt_ist = annotation_dt_utc.astimezone(IST)
                            annotation_dt_str = annotation_dt_ist.strftime('%Y-%m-%d %H:%M:%S IST')

                            # Enhanced annotation line
                            output_lines.append(
                                f"  NE: {tag_label}, Phrase: '{tag_text}', Annotator: {annotated_by}, Date: {annotation_dt_str}, ID: {tag_doc.get('_id', 'N/A')}"
                            )

                    output_lines.append("") # Empty line for separation

            output.write('\n'.join(output_lines))

            response = Response(output.getvalue(), mimetype='text/plain')
            filename = f"{project['name']}_{report_type}_report_{get_ist_time().strftime('%Y%m%d')}.txt"
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"
            return response

        # --- Enhanced XML Export Format ---
        elif file_format.upper() == "XML":
            print(f"DEBUG: Generating enhanced XML export for {len(unique_sentences)} sentences")
            
            root = etree.Element("project")
            
            # Enhanced project metadata
            metadata = etree.SubElement(root, "metadata")
            etree.SubElement(metadata, "name").text = project.get("name", "")
            etree.SubElement(metadata, "description").text = project.get("description", "")
            etree.SubElement(metadata, "language").text = project.get("language", "Unknown")
            etree.SubElement(metadata, "total_sentences").text = str(project_stats["total_sentences"])
            etree.SubElement(metadata, "annotated_sentences").text = str(project_stats["annotated_sentences"])
            etree.SubElement(metadata, "total_annotations").text = str(project_stats["total_annotations"])
            etree.SubElement(metadata, "unique_annotators").text = str(project_stats["unique_annotators"])
            etree.SubElement(metadata, "export_date").text = get_ist_time().isoformat()
            
            sentences_tag = etree.SubElement(root, "sentences")
            
            # Collect all sentence IDs for tag lookup
            all_sentence_ids = [str(item["sentence_data"]["_id"]) for item in unique_sentences]
            
            # Fetch all tags for these sentences
            all_tags = list(tags_collection.find({"source_sentence_id": {"$in": all_sentence_ids}}))
            print(f"DEBUG: Found {len(all_tags)} tags for enhanced XML export")
            
            # Create enhanced annotation map
            annotation_map = {}
            for tag in all_tags:
                sid = tag.get("source_sentence_id")
                if sid:
                    if sid not in annotation_map:
                        annotation_map[sid] = []
                    
                    # Enhanced annotation data
                    annotated_on_date = tag.get('annotation_date', get_ist_time())
                    annotated_on_str = annotated_on_date.strftime('%Y-%m-%d %H:%M:%S')
                    
                    annotation_map[sid].append({
                        "id": str(tag["_id"]),
                        "word_phrase": tag['text'],
                        "annotation": tag['tag'],
                        "annotated_by": tag.get('username', 'Unknown'), 
                        "annotated_on": annotated_on_str,
                        "annotation_date_iso": annotated_on_date.isoformat()
                    }) 
            
            for item in unique_sentences:
                sentence = item["sentence_data"]
                sentence_id_str = str(sentence["_id"])
                
                # Enhanced sentence element with more attributes
                sentence_tag = etree.SubElement(
                    sentences_tag, 
                    "sentence", 
                    id=sentence_id_str,
                    text=sentence["textContent"], 
                    isAnnotated="True" if item.get("is_annotated_any") else "False", 
                    project_id=project_id,
                    original_index=str(sentence.get("original_index", "")),
                    annotators=",".join(set(item.get("all_annotators", [])))
                )
                
                # Add annotations if they exist
                tags_data = annotation_map.get(sentence_id_str, [])
                print(f"DEBUG: Sentence {sentence_id_str} has {len(tags_data)} tags")
                
                if tags_data:
                    annotations_tag = etree.SubElement(sentence_tag, "annotations")
                    annotations_tag.set("count", str(len(tags_data)))
                    
                    for tag_doc in tags_data:
                        # Enhanced annotation element
                        etree.SubElement(
                            annotations_tag, 
                            "annotation", 
                            id=tag_doc['id'],
                            word_phrase=tag_doc['word_phrase'],
                            annotation=tag_doc['annotation'],
                            annotated_by=tag_doc['annotated_by'],
                            annotated_on=tag_doc['annotated_on'],
                            annotation_date_iso=tag_doc['annotation_date_iso']
                        )

            xml_string = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
            
            response = Response(xml_string, mimetype='application/xml')
            filename = f"{project['name']}_comprehensive_export_{get_ist_time().strftime('%Y%m%d')}.xml"
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"
            return response

        return jsonify({"error": "Invalid file format requested. Use 'Text' or 'XML'."}), 400

    except Exception as e:
        print(f"Backend CRASH during enhanced download: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return jsonify({"error": f"Download processing failed due to server error: {str(e)}"}), 500
    
     
@app.route("/sentences/<username>", methods=["GET"])
@token_required 
def get_sentences(username):
    """
    Fetches ALL sentences assigned to the user, separated into 
    'ad_hoc' and 'project_tasks' for the User Dashboard (Dashboard.js).
    """
    ad_hoc_sentences = []
    project_tasks = {}
    
    # Fetch all sentences assigned to the user
    for s in sentences_collection.find({"username": username}).sort([("project_id", 1), ("original_index", 1)]):
        
        # Prepare sentence data
        sentence_data = {
            "is_annotated": s.get("is_annotated", False),
            "_id": str(s["_id"]),
            "textContent": s["textContent"],
            "project_id": s.get("project_id"),
            "original_index": s.get("original_index")
        }
        
        project_id = s.get("project_id")
        
        if project_id is None:
            ad_hoc_sentences.append(sentence_data)
        else:
            project_id_str = str(project_id) # Ensure key is always a string
            
            # Fetch project name only once
            if project_id_str not in project_tasks:
                project_doc = None
                try:
                    project_doc = projects_collection.find_one({"_id": ObjectId(project_id_str)}, {"name": 1})
                except:
                    project_doc = projects_collection.find_one({"_id": project_id_str}, {"name": 1})

                project_name = project_doc['name'] if project_doc else "Unknown Project"
                
                # Initialize the structure expected by the frontend's project cards (Dashboard.js)
                project_tasks[project_id_str] = {
                    "project_name": project_name,
                    "sentences": [],
                    "total": 0,    # Will be updated below
                    "completed": 0 # Will be updated below
                }
            
            # Add sentence to the corresponding project group
            project_tasks[project_id_str]["sentences"].append(sentence_data)
            project_tasks[project_id_str]["total"] += 1
            if sentence_data["is_annotated"]:
                project_tasks[project_id_str]["completed"] += 1

    # Convert dictionary of projects into a list for JSON output
    project_tasks_list = list(project_tasks.values())
    
    # Return separated data structure
    return jsonify({
        "ad_hoc_sentences": ad_hoc_sentences,
        "project_tasks": project_tasks_list
    })

@app.route("/api/projects/<project_id>/users_and_progress", methods=["GET"])
def get_project_users_and_progress(project_id):
    """Get project users and their progress - COMPLETE FIX"""
    try:
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # FIXED: Proper aggregation to get user progress with review status
        pipeline = [
            {"$match": {"project_id": project_id}},
            {"$group": {
                "_id": "$username",
                "total": {"$sum": 1},
                "completed": {"$sum": {"$cond": ["$is_annotated", 1, 0]}},
                "reviewed": {"$sum": {"$cond": [
                    {"$in": ["$review_status", ["Approved", "Rejected", "Partially Approved"]]}, 
                    1, 0
                ]}}
            }},
            {"$project": {
                "username": "$_id",
                "total": 1,
                "completed": 1,
                "reviewed": 1,
                "_id": 0
            }},
            {"$sort": {"username": 1}}
        ]
        
        user_progress = list(sentences_collection.aggregate(pipeline))
        
        print(f"DEBUG: Project {project_id} user progress: {user_progress}")

        return jsonify({
            "project_name": project.get("name"),
            "users": user_progress
        }), 200

    except Exception as e:
        print(f"Error fetching project user progress: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
@app.route("/api/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    try:
        project_oid = ObjectId(project_id)
        project = projects_collection.find_one({"_id": project_oid})
        if not project:
            return jsonify({"message": "Project not found"}), 404

        project_string_id = str(project["_id"])

        # 1️⃣ Find all sentence IDs for this project
        sentences_to_delete = list(sentences_collection.find(
            {"project_id": project_string_id}, {"_id": 1}
        ))
        sentence_ids = [str(s["_id"]) for s in sentences_to_delete]

        # 2️⃣ Delete associated tags
        if sentence_ids:
            tags_collection.delete_many({"source_sentence_id": {"$in": sentence_ids}})
            search_tags_collection.delete_many({"source_sentence_id": {"$in": sentence_ids}})

        # 3️⃣ Delete all sentences for this project
        sentences_collection.delete_many({"project_id": project_string_id})

        # 4️⃣ Delete the project itself
        projects_collection.delete_one({"_id": project_oid})

        return jsonify({"message": f"Project '{project['name']}' and related data deleted successfully."}), 200
    except Exception as e:
        print(f"Error deleting project: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/projects/<project_id>", methods=["PUT"])
def update_project(project_id):
    """Update project details (name, description, language) and reassign to users"""
    try:
        data = request.json
        admin_username = data.get("adminUsername")
        
        if not admin_username:
            return jsonify({"error": "Admin username is required"}), 400

        # Find the project
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Prepare update fields
        update_fields = {}
        if "name" in data:
            update_fields["name"] = data["name"]
        if "description" in data:
            update_fields["description"] = data["description"]
        if "language" in data:
            update_fields["language"] = data["language"]

        # Update project details
        if update_fields:
            projects_collection.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": update_fields}
            )

        # Handle user reassignment if provided
        new_users = data.get("assigned_users", [])
        users_to_remove = data.get("users_to_remove", [])
        
        if new_users:
            # Assign new users to the project
            for username in new_users:
                # Check if user already has assignments for this project
                existing_assignments = sentences_collection.count_documents({
                    "project_id": project_id,
                    "username": username
                })
                
                if existing_assignments == 0:
                    # Get unique sentences from the project
                    unique_sentences = list(sentences_collection.aggregate([
                        {"$match": {"project_id": project_id}},
                        {"$group": {
                            "_id": {
                                "textContent": "$textContent",
                                "original_index": "$original_index"
                            },
                            "sentence_data": {"$first": "$$ROOT"}
                        }}
                    ]))
                    
                    # Create new assignments for the user
                    for unique_sentence in unique_sentences:
                        sentence_data = unique_sentence["sentence_data"]
                        new_sentence = {
                            "username": username,
                            "textContent": sentence_data["textContent"],
                            "is_annotated": False,  # New assignments start as unannotated
                            "annotation_tags": [],
                            "annotation_email": None,
                            "annotation_datetime": None,
                            "project_id": project_id,
                            "original_index": sentence_data.get("original_index")
                        }
                        sentences_collection.insert_one(new_sentence)

        # Remove users from project if specified
        if users_to_remove:
            for username in users_to_remove:
                # Find sentences to be removed
                sentences_to_delete = list(sentences_collection.find(
                    {"project_id": project_id, "username": username},
                    {"_id": 1}
                ))
                sentence_ids = [str(s["_id"]) for s in sentences_to_delete]
                
                # Delete sentences and associated tags
                sentences_collection.delete_many({
                    "project_id": project_id,
                    "username": username
                })
                
                if sentence_ids:
                    tags_collection.delete_many({"source_sentence_id": {"$in": sentence_ids}})
                    search_tags_collection.delete_many({"source_sentence_id": {"$in": sentence_ids}})

        # Log the action
        log_action_and_update_report(
            admin_username, 
            f"Updated project '{project['name']}' (ID: {project_id})"
        )

        return jsonify({"message": "Project updated successfully"}), 200

    except Exception as e:
        print(f"Error updating project: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
 

@app.route("/api/projects/<project_id>/sentences", methods=["GET"])
def get_project_sentences(project_id):
    """
    Fetches sentences and their tags (BOTH final and staged) for a specific project ID and user.
    """
    try:
        from bson.objectid import ObjectId
        from datetime import datetime
        project_name = "Unknown Project"
        try:
            # To this:
            try:
                project = projects_collection.find_one({"_id": ObjectId(project_id)})
            except:
                # If ObjectId fails, try finding by string ID
                project = projects_collection.find_one({"_id": project_id})
            if project:
                project_name = project["name"]
        except:
            pass

        target_username = request.args.get("username")
        if not target_username:
            return jsonify({"error": "Target username is required for sentence review."}), 400
            
        print(f"DEBUG: Fetching sentences for project {project_id}, user {target_username}")
            
        # Fetch sentences with their FINAL tags
        pipeline = [
            {"$match": {
                "project_id": project_id, 
                "username": target_username
            }},
            {"$addFields": {
                "sentence_id_str": {"$toString": "$_id"}
            }},
            {"$lookup": {
                "from": "tags",
                "localField": "sentence_id_str",
                "foreignField": "source_sentence_id", 
                "as": "final_tags"
            }},
            {"$sort": {"original_index": 1}}
        ]
        
        project_sentences = []
        cursor = sentences_collection.aggregate(pipeline)
        
        for s in cursor:
            sentence_id_str = str(s["_id"])
            
            # Fetch STAGED tags for this sentence using your existing route logic
            staged_tags = list(staged_tags_collection.find({
                "source_sentence_id": sentence_id_str 
            }))
            
            # --- BEGIN: MODIFIED LOGIC BLOCK ---
            
            # Determine if the annotator has touched the sentence at all
            is_annotated_from_tags = len(s.get("final_tags", [])) > 0 or len(staged_tags) > 0
            
     
            overall_review_status = s.get("review_status", "Pending")
            
            # --- END: MODIFIED LOGIC BLOCK ---

            # Combine final tags and staged tags
            all_tags = []
            
            # Process final tags
            for tag in s.get("final_tags", []):
                tag_data = {
                    "text": tag.get("text", ""),
                    "tag": tag.get("tag", ""),
                    "username": tag.get("username", ""),
                    "annotation_date": tag.get("annotation_date"),
                    "neId": tag.get("neId"),
                    "_id": str(tag["_id"]),
                    "review_status": "Approved", 
                    "review_comments": tag.get("review_comments", "")
                }
                if tag_data["annotation_date"] and isinstance(tag_data["annotation_date"], datetime):
                    tag_data["annotated_on"] = tag_data["annotation_date"].strftime('%Y-%m-%d')
                all_tags.append(tag_data)
            
            # Process staged tags
            for tag in staged_tags:
                tag_data = {
                    "text": tag.get("text", ""),
                    "tag": tag.get("tag", ""),
                    "username": tag.get("username", ""),
                    "annotation_date": tag.get("annotation_date"),
                    "neId": tag.get("neId"),
                    "_id": str(tag["_id"]),
                    "review_comments": tag.get("review_comments", "")
                }

                # Determine review status
                if tag.get("review_status") == "Rejected":
                    tag_data["review_status"] = "Rejected"
                elif tag_data["username"] == "auto_annotator_system": 
                    tag_data["review_status"] = "Approved" 
                else:
                    tag_data["review_status"] = "Pending"

                if tag_data["annotation_date"] and isinstance(tag_data["annotation_date"], datetime):
                    tag_data["annotated_on"] = tag_data["annotation_date"].strftime('%Y-%m-%d')
                all_tags.append(tag_data)
            
            # Convert MongoDB document to JSON-serializable format
            sentence_data = {
                "_id": str(s["_id"]),
                "textContent": s["textContent"],
                # Use calculated value if DB flag isn't set
                "is_annotated": s.get("is_annotated", False) or is_annotated_from_tags,
                "original_index": s.get("original_index"),
                "project_id": s.get("project_id"),
                "username": s.get("username"),
                "annotation_datetime": s.get("annotation_datetime"),
                "annotation_email": s.get("annotation_email"),
                "tags": all_tags,
                "review_status": overall_review_status
            }
            
            
            project_sentences.append(sentence_data)
            
        print(f"DEBUG: Found {len(project_sentences)} sentences with {sum(len(s['tags']) for s in project_sentences)} total tags")
            
        return jsonify({
            "project_name": project_name,
            "sentences": project_sentences
        }), 200
        
    except Exception as e:
        print(f"Error fetching project sentences for review: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal server error while fetching sentences: {str(e)}"}), 500
          
@app.route('/api/activity-logs/<username>', methods=["GET"])
def get_activity_logs(username):
    """Fetches activity history for the given username (admin required)."""
    try:
        # Authorization check - the requesting user must be admin
        requesting_user = users_collection.find_one({"username": username})
        if not requesting_user or requesting_user.get("role") != "admin":
            return jsonify({"message": "Unauthorized access"}), 403

        # Get target username from query parameter (if provided)
        target_username = request.args.get('target_user')
        
        all_history = []
        
        if target_username:
            # Fetch logs for specific user
            user_doc = user_session_history_collection.find_one({"username": target_username})
            if user_doc:
                for session in user_doc.get('sessions', []):
                    all_history.append({
                        "id": f"{user_doc['username']}_{session.get('loginTimeIST', '')}",
                        "username": user_doc['username'],
                        **session
                    })
        else:
            # Fetch logs for ALL users (current behavior)
            for user_doc in user_session_history_collection.find():
                for session in user_doc.get('sessions', []):
                    all_history.append({
                        "id": f"{user_doc['username']}_{session.get('loginTimeIST', '')}",
                        "username": user_doc['username'],
                        **session
                    })

        # Sort by login time, descending
        all_history.sort(key=lambda x: datetime.strptime(x['loginTimeIST'], '%d/%m/%Y, %H:%M:%S') if x['loginTimeIST'] else datetime.min, reverse=True)
        return jsonify(all_history)
        
    except Exception as e:
        print(f"Error fetching activity logs: {e}")
        return jsonify({"error": "Internal server error"}), 500
     
    
@app.route('/sentences/<sentence_id>/tags/<tag_id>', methods=['DELETE'])
def remove_tag_from_sentence(sentence_id, tag_id):
    try:
        result = tags_collection.delete_one({"_id": ObjectId(tag_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Tag not found"}), 404

        sentence = sentences_collection.find_one({"_id": ObjectId(sentence_id)})
        if sentence:
            username = sentence.get("username")
            log_action_and_update_report(username, f"Removed tag {tag_id} from sentence '{sentence.get('textContent','')}'")

        return jsonify({"message": "Tag removed successfully"}), 200
    except Exception as e:
        print(f"Error removing tag: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500
   
@app.route('/api/tags/<tag_id>', methods=['DELETE'])
def remove_any_tag(tag_id):
    """Remove any tag (both staged and approved)"""
    try:
        # First try to delete from staged tags
        staged_result = staged_tags_collection.delete_one({"_id": ObjectId(tag_id)})
        
        if staged_result.deleted_count > 0:
            # Get tag info for logging
            staged_tag = staged_tags_collection.find_one({"_id": ObjectId(tag_id)})
            if staged_tag:
                sentence_id = staged_tag.get('source_sentence_id')
                username = staged_tag.get('username')
                # Update sentence review status
                update_sentence_review_status(sentence_id)
                # Log the action
                if username:
                    log_action_and_update_report(username, f"Removed staged tag '{staged_tag.get('text', '')}'")
            
            return jsonify({"message": "Staged tag removed successfully"}), 200
        
        # If not found in staged, try approved tags
        approved_result = tags_collection.delete_one({"_id": ObjectId(tag_id)})
        if approved_result.deleted_count > 0:
            # Also delete from search_tags
            search_tags_collection.delete_one({"_id": ObjectId(tag_id)})
            return jsonify({"message": "Approved tag removed successfully"}), 200
        
        return jsonify({"message": "Tag not found"}), 404
        
    except Exception as e:
        print(f"Error removing tag: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
@app.route('/tags', methods=['POST'])
def add_or_update_tag():
    """
    MODIFIED: Annotator adds/updates a tag. It now writes directly to tags_collection.
    Only when sentence is submitted for review, tags become "pending".
    """
    try:
        data = request.get_json()
        required_fields = ['username', 'text', 'tag', 'sentenceId']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields in request'}), 400

        username = data['username']
        text = data['text']
        tag_label = data['tag']
        sentence_id = data['sentenceId']

        IST = ZoneInfo("Asia/Kolkata") 

        # Check if sentence is submitted for review
        sentence = sentences_collection.find_one({"_id": ObjectId(sentence_id)})
        is_pending_review = sentence and sentence.get('review_status') == 'PENDING_REVIEW'

        tag_data = {
            'tag': tag_label,
            'source_sentence_id': sentence_id,
            'username': username,
            'text': text,
            'annotation_date': datetime.now(IST),
        }

        if is_pending_review:
            # If sentence is pending review, tag goes to staged_tags with pending status
            tag_data['review_status'] = 'Pending'
            tag_data['status'] = 'Staged/Pending Review'
            
            # Check if tag already exists in staged_tags
            existing_staged_tag = staged_tags_collection.find_one({
                'source_sentence_id': sentence_id, 
                'username': username,
                'text': text
            })
            
            if existing_staged_tag:
                staged_tags_collection.update_one(
                    {'_id': existing_staged_tag['_id']},
                    {'$set': tag_data}
                )
                message = 'Tag updated in staging (pending review)'
            else:
                staged_tags_collection.insert_one(tag_data)
                message = 'Tag created and staged (pending review)'
                
        else:
            # Normal case - tag goes directly to approved tags
            tag_data['review_status'] = 'Approved'
            tag_data['reviewed_by'] = 'auto_approved'
            tag_data['reviewed_at'] = datetime.now(IST)
            
            # Check if tag already exists in tags
            existing_tag = tags_collection.find_one({
                'source_sentence_id': sentence_id, 
                'username': username,
                'text': text
            })
            
            if existing_tag:
                tags_collection.update_one(
                    {'_id': existing_tag['_id']},
                    {'$set': tag_data}
                )
                # Also update search_tags
                search_tags_collection.update_one(
                    {'_id': existing_tag['_id']},
                    {'$set': tag_data}
                )
                message = 'Tag updated successfully'
            else:
                result = tags_collection.insert_one(tag_data)
                # Also insert into search_tags
                search_tags_collection.insert_one(tag_data)
                message = 'Tag created successfully'

        # Update sentence annotation status
        sentences_collection.update_one(
            {'_id': ObjectId(sentence_id)},
            {'$set': {
                'is_annotated': True,
                'annotation_email': username,
                'annotation_datetime': get_ist_time()
            }}
        )

        log_action_and_update_report(username, f"Added tag '{text}' as '{tag_label}'")
        return jsonify({'message': message}), 200
        
    except Exception as e:
        print(f"Error in /tags POST endpoint: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
 
@app.route('/reviewer/sentence/<sentence_id>/tags', methods=['GET'])
def get_staged_tags_for_review(sentence_id):
    """
    Fetches all staged tags for a specific sentence ID for review.
    """
    try:
        # 1. Query the staged_tags collection for the sentence
        # We use the sentence_id provided in the URL path.
        staged_tags = list(staged_tags_collection.find({
            "sentence_id": sentence_id
        }))

        # 2. Prepare data for the frontend (convert ObjectId to string)
        for tag in staged_tags:
            # Convert MongoDB's ObjectId to a string for JSON serialization
            tag['_id'] = str(tag['_id'])
            
            # Ensure sentence_id is a string, if needed
            if 'sentence_id' in tag and not isinstance(tag['sentence_id'], str):
                 tag['sentence_id'] = str(tag['sentence_id'])

        return jsonify(staged_tags), 200

    except Exception as e:
        print(f"Error fetching staged tags for review: {e}")
        return jsonify({"error": "Internal server error during tag retrieval."}), 500

@app.route('/reviewer/tag/<tag_id>/approve', methods=['PUT'])
def approve_tag(tag_id):
    try:
        data = request.json
        reviewer_username = data.get('reviewerUsername')
        
        staged_tag = staged_tags_collection.find_one({"_id": ObjectId(tag_id)})
        if not staged_tag:
            return jsonify({"message": "Staged tag not found or already reviewed."}), 404
            
        sentence_id = staged_tag.get('source_sentence_id')
        annotator_username = staged_tag.get('username')
        
        # Create final tag with updated status
        final_tag = {
            'tag': staged_tag.get('tag'),
            'source_sentence_id': staged_tag.get('source_sentence_id'),
            'username': staged_tag.get('username'),
            'text': staged_tag.get('text'),
            'annotation_date': staged_tag.get('annotation_date'),
            'review_status': 'Approved',  
            'review_comments': data.get('comments', ''),
            'reviewed_by': reviewer_username,
            'reviewed_at': get_ist_time()
        }
        
        # Insert into final collections
        tags_collection.insert_one(final_tag)

        # Remove from staged collection
        staged_tags_collection.delete_one({"_id": ObjectId(tag_id)})
        
        # Update sentence review status
        update_sentence_review_status(sentence_id)
        
        # Log the action for BOTH reviewer and annotator
        log_action_and_update_report(reviewer_username, 
                                   f"Approved tag '{final_tag.get('text')}' by {annotator_username}.")
        log_action_and_update_report(annotator_username, 
                                   f"Tag '{final_tag.get('text')}' was approved by reviewer {reviewer_username}.")

        return jsonify({"message": "Tag approved and finalized successfully."}), 200
    except Exception as e:
        print(f"Error approving tag: {e}")
        return jsonify({"error": "Internal server error during tag approval."}), 500

@app.route('/reviewer/tag/<tag_id>/undo-approval', methods=['POST'])
def undo_tag_approval(tag_id):
    """Move an approved tag back to staging for re-review"""
    try:
        data = request.json
        reviewer_username = data.get('reviewerUsername')
        
        # Find the approved tag
        approved_tag = tags_collection.find_one({"_id": ObjectId(tag_id)})
        if not approved_tag:
            return jsonify({"message": "Approved tag not found."}), 404
            
        sentence_id = approved_tag.get('source_sentence_id')
        annotator_username = approved_tag.get('username')
        
        # Create staged tag from the approved tag data
        staged_tag = {
            'tag': approved_tag.get('tag'),
            'source_sentence_id': approved_tag.get('source_sentence_id'),
            'username': approved_tag.get('username'),
            'text': approved_tag.get('text'),
            'annotation_date': approved_tag.get('annotation_date'),
            'status': 'Staged/Pending Review',
            'previous_review': {
                'was_approved': True,
                'reviewed_by': approved_tag.get('reviewed_by'),
                'reviewed_at': approved_tag.get('reviewed_at'),
                'review_comments': approved_tag.get('review_comments', ''),
                'undone_by': reviewer_username,
                'undone_at': get_ist_time()
            }
        }
        
        # Insert back to staged collection
        staged_tags_collection.insert_one(staged_tag)
        
        # Remove from final collections
        tags_collection.delete_one({"_id": ObjectId(tag_id)})
        search_tags_collection.delete_one({"_id": ObjectId(tag_id)})
        
        # Update sentence review status
        update_sentence_review_status(sentence_id)
        
        # Log the action for BOTH reviewer and annotator
        log_action_and_update_report(reviewer_username, 
                                   f"Undid approval of tag '{approved_tag.get('text')}' by {annotator_username}.")
        log_action_and_update_report(annotator_username, 
                                   f"Tag '{approved_tag.get('text')}' approval was undone by reviewer {reviewer_username}.")

        return jsonify({"message": "Tag approval undone successfully. Tag moved back to staging."}), 200
        
    except Exception as e:
        print(f"Error undoing tag approval: {e}")
        return jsonify({"error": "Internal server error during undo operation."}), 500

@app.route('/reviewer/tag/<tag_id>/undo-rejection', methods=['POST'])
def undo_tag_rejection(tag_id):
    """Move a rejected tag back to pending status"""
    try:
        data = request.json
        reviewer_username = data.get('reviewerUsername')
        
        # Find the rejected tag
        rejected_tag = staged_tags_collection.find_one({"_id": ObjectId(tag_id)})
        if not rejected_tag:
            return jsonify({"message": "Rejected tag not found."}), 404
            
        sentence_id = rejected_tag.get('source_sentence_id')
        annotator_username = rejected_tag.get('username')
        
        # Move back to pending status
        staged_tags_collection.update_one(
            {"_id": ObjectId(tag_id)},
            {"$set": {
                "review_status": "Pending",
                "review_comments": "",
                "reviewed_by": "",
                "reviewed_at": None
            }}
        )
        
        # Update sentence review status
        update_sentence_review_status(sentence_id)
        
        # Log the action for BOTH reviewer and annotator
        log_action_and_update_report(reviewer_username, 
                                   f"Undid rejection of tag '{rejected_tag.get('text')}' by {annotator_username}.")
        log_action_and_update_report(annotator_username, 
                                   f"Tag '{rejected_tag.get('text')}' rejection was undone by reviewer {reviewer_username}.")

        return jsonify({"message": "Tag rejection undone successfully. Tag moved back to pending."}), 200
        
    except Exception as e:
        print(f"Error undoing tag rejection: {e}")
        return jsonify({"error": "Internal server error during undo operation."}), 500

@app.route('/reviewer/tag/<tag_id>/reject', methods=['DELETE'])
def reject_tag(tag_id):
    try:
        data = request.json
        reviewer_username = data.get('reviewerUsername')
        comments = data.get('comments', '')
        
        staged_tag = staged_tags_collection.find_one({"_id": ObjectId(tag_id)})
        if not staged_tag:
            return jsonify({"message": "Staged tag not found."}), 404
            
        sentence_id = staged_tag.get('source_sentence_id')
        annotator_username = staged_tag.get('username')
        
        # Instead of deleting, mark as rejected
        staged_tags_collection.update_one(
            {"_id": ObjectId(tag_id)},
            {"$set": {
                "review_status": "Rejected",
                "review_comments": comments,
                "reviewed_by": reviewer_username,
                "reviewed_at": get_ist_time()
            }}
        )
        
        final_tag = {
            'tag': staged_tag.get('tag'),
            'source_sentence_id': staged_tag.get('source_sentence_id'),
            'username': staged_tag.get('username'),
            'text': staged_tag.get('text'),
            'annotation_date': staged_tag.get('annotation_date'),
            'review_status': 'Rejected',  
            'review_comments': data.get('comments', ''),
            'reviewed_by': reviewer_username,
            'reviewed_at': get_ist_time()
        }
        
        # Insert into final collections
        tags_collection.delete_one(final_tag)
        
        # Update sentence status
        update_sentence_review_status(sentence_id)
        
        # Log the action for BOTH reviewer and annotator
        log_action_and_update_report(reviewer_username, 
                                   f"Rejected tag '{staged_tag.get('text')}' by {annotator_username}.")
        log_action_and_update_report(annotator_username, 
                                   f"Tag '{staged_tag.get('text')}' was rejected by reviewer {reviewer_username}.")

        return jsonify({"message": "Tag rejected successfully."}), 200
    except Exception as e:
        print(f"Error rejecting tag: {e}")
        return jsonify({"error": "Internal server error during tag rejection."}), 500  
 
    
@app.route('/tags/<username>', methods=['GET'])
def get_tags(username):
    """
    FIXED: Gets only approved tags for sentences assigned to the user
    Rejected tags are filtered out and not shown to the user
    """
    try:
        print(f"DEBUG: Fetching tags for user: {username}")
        
        # First, get all sentence IDs assigned to this user
        user_sentences = list(sentences_collection.find(
            {"username": username}, 
            {"_id": 1}
        ))
        user_sentence_ids = [str(sentence["_id"]) for sentence in user_sentences]
        
        print(f"DEBUG: User {username} has {len(user_sentence_ids)} sentences: {user_sentence_ids}")
        
        if not user_sentence_ids:
            print(f"DEBUG: No sentences found for user {username}")
            return jsonify([])
        
        # Get final approved tags (ONLY approved ones)
        final_tags = list(tags_collection.find({
            'source_sentence_id': {'$in': user_sentence_ids},
            'review_status': 'Approved'  # ONLY return approved tags
        }))
        
        # Get staged/pending tags (ONLY pending ones, exclude rejected)
        staged_tags = list(staged_tags_collection.find({
            'source_sentence_id': {'$in': user_sentence_ids},
            'review_status': {'$ne': 'Rejected'}  # Exclude rejected tags
        }))
        
        print(f"DEBUG: Found {len(final_tags)} approved tags and {len(staged_tags)} pending tags (rejected tags filtered out)")
        
        user_tags = []
        
        # Process final approved tags
        for tag in final_tags:
            tag_data = {
                "_id": str(tag["_id"]),
                "text": tag.get("text", ""),
                "tag": tag.get("tag", ""),
                "source_sentence_id": tag.get("source_sentence_id", ""),
                "username": tag.get("username", ""),
                "annotation_date": tag.get("annotation_date"),
                "status": "approved",
                "review_status": "Approved"
            }
            user_tags.append(tag_data)
        
        # Process staged/pending tags (excluding rejected)
        for tag in staged_tags:
            # Double check to exclude any rejected tags that might slip through
            if tag.get("review_status") != "Rejected":
                tag_data = {
                    "_id": str(tag["_id"]),
                    "text": tag.get("text", ""),
                    "tag": tag.get("tag", ""),
                    "source_sentence_id": tag.get("source_sentence_id", ""),
                    "username": tag.get("username", ""),
                    "annotation_date": tag.get("annotation_date"),
                    "status": "pending",
                    "review_status": tag.get("review_status", "Pending"),
                    "review_comments": tag.get("review_comments", "")
                }
                user_tags.append(tag_data)
        
        print(f"DEBUG: Returning {len(user_tags)} total tags for user {username} (rejected tags filtered out)")
        
        return jsonify(user_tags)
        
    except Exception as e:
        print(f"Error in get_tags: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500
        
@app.route("/sentences/<sentence_id>/status", methods=["PUT"])
def update_sentence_status(sentence_id):
    data = request.json
    new_status = data.get('is_annotated')
    username = data.get('username') 
    
    if new_status is None: return jsonify({"error": "is_annotated status is required"}), 400
    if not username: return jsonify({"error": "Username is required for status update and logging."}), 400
    
    update_fields = {"is_annotated": new_status}
    IST = ZoneInfo("Asia/Kolkata") 
    
    # Capture Annotated by (Email) and Annotation Date/Time upon annotation
    if new_status:
        user_doc = users_collection.find_one({"username": username})
        user_email = user_doc.get("email") if user_doc else None
        
        update_fields["annotation_email"] = user_email
        update_fields["annotation_datetime"] = datetime.now(IST)
    else:
        # Clear metadata if un-annotating
        update_fields["annotation_email"] = None
        update_fields["annotation_datetime"] = None
        
    result = sentences_collection.update_one(
            {"_id": ObjectId(sentence_id)}, {"$set": update_fields}
        )
        
    if result.matched_count == 0: return jsonify({"message": "Sentence not found"}), 404
    
    # Log the action
    sentence = sentences_collection.find_one({"_id": ObjectId(sentence_id)})
    if sentence:
        status_text = "Yes" if new_status else "No"
        log_action_and_update_report(username, f"Marked sentence '{sentence['textContent']}' as Annotated: {status_text}")
        
    return jsonify({"message": "Status updated successfully"})

@app.route('/api/sentence/submit_for_review', methods=['POST'])
@token_required
def submit_for_review():
    """
    Endpoint 1: Annotator's Action - Pushes the tagged sentence to the Reviewer's queue.
    Moves all approved tags to staged_tags with pending status.
    """
    try:
        data = request.get_json()
        sentence_id = data.get('sentence_id')
        annotator_username = request.current_user['username'] 

        if not sentence_id:
            return jsonify({"error": "Missing sentence ID"}), 400

        print(f"DEBUG: Submitting sentence {sentence_id} for review by {annotator_username}")

        # First, verify the sentence exists and belongs to the annotator
        sentence = sentences_collection.find_one({
            "_id": ObjectId(sentence_id), 
            "username": annotator_username
        })
        
        if not sentence:
            print(f"DEBUG: Sentence {sentence_id} not found or not assigned to user {annotator_username}")
            return jsonify({"message": "Sentence not found or not assigned to this user"}), 404

        # Move all approved tags for this sentence to staged_tags with pending status
        approved_tags = list(tags_collection.find({
            "source_sentence_id": sentence_id,
            "username": annotator_username
        }))
        
        if approved_tags:
            # Convert approved tags to staged tags with pending status
            staged_tags_to_insert = []
            for tag in approved_tags:
                staged_tag = {
                    'tag': tag.get('tag'),
                    'source_sentence_id': tag.get('source_sentence_id'),
                    'username': tag.get('username'),
                    'text': tag.get('text'),
                    'annotation_date': tag.get('annotation_date'),
                    'review_status': 'Pending',
                    'status': 'Staged/Pending Review',
                    'original_tag_id': str(tag['_id'])  # Keep reference to original
                }
                staged_tags_to_insert.append(staged_tag)
            
            # Insert into staged_tags
            if staged_tags_to_insert:
                staged_tags_collection.insert_many(staged_tags_to_insert)
                
            # Remove from approved tags
            tags_collection.delete_many({
                "source_sentence_id": sentence_id,
                "username": annotator_username
            })
            search_tags_collection.delete_many({
                "source_sentence_id": sentence_id, 
                "username": annotator_username
            })

        # Update the Sentence status to PENDING_REVIEW
        result = sentences_collection.update_one(
            {"_id": ObjectId(sentence_id), "username": annotator_username},
            {"$set": {
                "review_status": "PENDING_REVIEW",
                "submission_date": get_ist_time()
            }}
        )

        if result.matched_count == 0:
            print(f"DEBUG: No sentence matched for update: {sentence_id}")
            return jsonify({"message": "Sentence not found or not assigned to this user"}), 404
        
        print(f"DEBUG: Successfully submitted sentence {sentence_id} for review")
        log_action_and_update_report(annotator_username, f'Submitted sentence {sentence_id} for review.')

        return jsonify({"message": f"Sentence {sentence_id} submitted successfully for review."}), 200

    except Exception as e:
        print(f"Error submitting sentence for review: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error during submission"}), 500

@app.route('/api/reviewer/pending_sentences', methods=['GET'])
@token_required
def get_pending_sentences():
    """
    Endpoint 2: Reviewer Dashboard Fetch - Pulls ONLY sentences that have been submitted for review.
    """
    try:
        # ONLY match sentences that have been explicitly submitted for review
        pipeline = [
            {"$match": {
                "review_status": "PENDING_REVIEW"  # ONLY get sentences explicitly submitted for review
            }},
            
            # Fetch Project Name
            {"$lookup": {
                "from": "projects",
                "localField": "project_id",
                "foreignField": "_id",
                "as": "project_info"
            }},
            {"$unwind": {"path": "$project_info", "preserveNullAndEmptyArrays": True}},
            
            {"$sort": {"submission_date": 1, "_id": 1}},
            
            # Project fields to match the frontend structure
            {"$project": {
                "id": {"$toString": "$_id"},
                "sentence_text": "$textContent",
                "annotatorUsername": "$username",
                "projectId": {"$toString": "$project_id"},
                "project_name": "$project_info.name",
                "isAnnotated": "$is_annotated",
                "review_status": "$review_status",
                "submission_date": "$submission_date"
            }}
        ]
        
        pending_sentences = list(sentences_collection.aggregate(pipeline))
        
        print(f"DEBUG: Found {len(pending_sentences)} sentences explicitly submitted for review")
        
        # Clean up the results to ensure all ObjectIds are converted to strings
        for sentence in pending_sentences:
            for key in list(sentence.keys()):
                if isinstance(sentence[key], ObjectId):
                    sentence[key] = str(sentence[key])
        
        # Enhanced tag retrieval - get both staged AND approved tags
        sentence_ids = [s['id'] for s in pending_sentences]
        
        # Get staged tags (pending review)
        staged_tags_cursor = staged_tags_collection.find({"source_sentence_id": {"$in": sentence_ids}})
        staged_tag_map = {}
        for tag in staged_tags_cursor:
            sid = tag['source_sentence_id']
            if sid not in staged_tag_map:
                staged_tag_map[sid] = []
            tag_data = {
                '_id': str(tag['_id']),
                'text': tag.get('text', ''),
                'tag': tag.get('tag', ''),
                'username': tag.get('username', ''),
                'review_status': tag.get('review_status', 'Pending'),
                'annotation_date': tag.get('annotation_date'),
                'source': 'staged'
            }
            staged_tag_map[sid].append(tag_data)

        # Get approved tags (already reviewed and approved)
        approved_tags_cursor = tags_collection.find({"source_sentence_id": {"$in": sentence_ids}})
        approved_tag_map = {}
        for tag in approved_tags_cursor:
            sid = tag['source_sentence_id']
            if sid not in approved_tag_map:
                approved_tag_map[sid] = []
            tag_data = {
                '_id': str(tag['_id']),
                'text': tag.get('text', ''),
                'tag': tag.get('tag', ''),
                'username': tag.get('username', ''),
                'review_status': tag.get('review_status', 'Approved'),
                'annotation_date': tag.get('annotation_date'),
                'reviewed_by': tag.get('reviewed_by', ''),
                'reviewed_at': tag.get('reviewed_at'),
                'source': 'approved'
            }
            approved_tag_map[sid].append(tag_data)

        # Combine both staged and approved tags for each sentence
        for sentence in pending_sentences:
            sid = sentence['id']
            all_tags = []
            
            # Add staged tags
            if sid in staged_tag_map:
                all_tags.extend(staged_tag_map[sid])
            
            # Add approved tags  
            if sid in approved_tag_map:
                all_tags.extend(approved_tag_map[sid])
            
            sentence['tags'] = all_tags
            print(f"DEBUG: Sentence {sid} has {len(all_tags)} tags ({len(staged_tag_map.get(sid, []))} staged, {len(approved_tag_map.get(sid, []))} approved)")
            
        return jsonify(pending_sentences), 200

    except Exception as e:
        print(f"Error fetching pending sentences for reviewer: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error during queue fetch"}), 500
      
@app.route('/api/sentence/review_action', methods=['POST'])
@token_required
def review_action():
    """
    Endpoint 3: Reviewer Action - Approves/Rejects a sentence (finalizes status).
    """
    try:
        data = request.get_json()
        sentence_id = data.get('sentence_id')
        action = data.get('action') # 'Approve' or 'Reject'
        comment = data.get('review_comment', '')
        
        reviewer_username = request.current_user['username']
        
        print(f"DEBUG REVIEW_ACTION: Starting for sentence {sentence_id}, action: {action}")
        print(f"DEBUG REVIEW_ACTION: Comment: {comment}")
        
        sentence = sentences_collection.find_one({"_id": ObjectId(sentence_id)})
        
        if not sentence:
            print(f"DEBUG REVIEW_ACTION: Sentence {sentence_id} not found")
            return jsonify({"error": "Sentence not found"}), 404
            
        annotator_username = sentence.get('username')
        print(f"DEBUG REVIEW_ACTION: Annotator username: {annotator_username}")
        
        if action == 'Approve':
            new_status = 'REVIEWED_APPROVED'
            
            # 1. Move staged tags to the final tags collection
            staged_tags_cursor = staged_tags_collection.find({"source_sentence_id": sentence_id, "username": annotator_username})
            tags_to_insert = []
            for tag in staged_tags_cursor:
                tags_to_insert.append({
                    'tag': tag.get('tag'), 'source_sentence_id': sentence_id, 'username': tag.get('username'),
                    'text': tag.get('text'), 'annotation_date': tag.get('annotation_date'),
                    "review_status": "Approved", "reviewed_by": reviewer_username,
                    "reviewed_at": get_ist_time(), "review_comments": comment
                })
            
            if tags_to_insert:
                print(f"DEBUG REVIEW_ACTION: Moving {len(tags_to_insert)} tags to final collection")
                tags_collection.insert_many(tags_to_insert)
                staged_tags_collection.delete_many({"source_sentence_id": sentence_id, "username": annotator_username})
            
            # 2. Update sentence status
            sentences_collection.update_one(
                {"_id": ObjectId(sentence_id)},
                {"$set": {"review_status": new_status, "reviewed_by": reviewer_username, "review_date": get_ist_time()}}
            )
            log_reviewer_action(reviewer_username, f"Approved sentence {sentence_id}", annotator_username)
            
            
        elif action == 'Reject':
            if not comment.strip():
                return jsonify({"error": "Review comment is mandatory for rejection"}), 400
            
            new_status = 'REVIEWED_REJECTED'
            
            print(f"DEBUG REVIEW_ACTION: Processing rejection for sentence {sentence_id}")
            
            # 1. Update sentence status
            sentences_collection.update_one(
                {"_id": ObjectId(sentence_id)},
                {"$set": {"review_status": new_status, "reviewed_by": reviewer_username, "review_date": get_ist_time()}}
            )
            
            # 2. Log the rejection comment (Revision Note)
            revision_note_data = {
                "sentence_id": sentence_id,
                "annotator_username": annotator_username,
                "reviewer_username": reviewer_username,
                "revision_comment": comment,
                "rejection_date": get_ist_time(),
                "acknowledged": False
            }
            
            print(f"DEBUG REVIEW_ACTION: Inserting revision note: {revision_note_data}")
            revision_result = revision_notes_collection.insert_one(revision_note_data)
            print(f"DEBUG REVIEW_ACTION: Revision note inserted with ID: {revision_result.inserted_id}")
            
            # 3. Mark all staged tags for this sentence as Rejected
            staged_update_result = staged_tags_collection.update_many(
                {"source_sentence_id": sentence_id, "username": annotator_username},
                {"$set": {"review_status": "Rejected", "review_comments": comment}}
            )
            print(f"DEBUG REVIEW_ACTION: Updated {staged_update_result.modified_count} staged tags as Rejected")
            
            log_reviewer_action(reviewer_username, f"Rejected sentence {sentence_id}", annotator_username)

        else:
            return jsonify({"error": "Invalid review action"}), 400

        print(f"DEBUG REVIEW_ACTION: Successfully completed {action} for sentence {sentence_id}")
        return jsonify({"message": f"Review finalized: {action}"}), 200

    except Exception as e:
        print(f"DEBUG REVIEW_ACTION: Error processing review action: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error during review finalization"}), 500
    
@app.route('/api/annotator/revision_notes/<string:username>', methods=["GET"])
@token_required
def get_revision_notes(username):
    """
    Endpoint 4: Annotator Fetch - Pulls rejected sentences with revision notes
    """
    try:
        # Verify the requesting user has access to these revision notes
        current_user = request.current_user
        if current_user.get('username') != username:
            return jsonify({"error": "Unauthorized access to revision notes"}), 403
        
        print(f"DEBUG REVISION_NOTES: Fetching revision notes for user: {username}")
        
        revision_notes = []
        
        # Get all unacknowledged revision notes for this user
        notes_cursor = revision_notes_collection.find({
            "annotator_username": username,
            "acknowledged": False
        })
        
        notes_list = list(notes_cursor)
        print(f"DEBUG REVISION_NOTES: Found {len(notes_list)} unacknowledged revision notes")
        
        for note in notes_list:
            sentence_id = note.get('sentence_id')
            print(f"DEBUG REVISION_NOTES: Processing note for sentence: {sentence_id}")
            
            try:
                # Get the sentence details
                sentence = sentences_collection.find_one({"_id": ObjectId(sentence_id)})
                if not sentence:
                    print(f"DEBUG REVISION_NOTES: Sentence {sentence_id} not found, skipping")
                    continue
                
                # Get rejected tags for this sentence
                rejected_tags_cursor = staged_tags_collection.find({
                    "source_sentence_id": sentence_id,
                    "username": username,
                    "review_status": "Rejected"
                })
                rejected_tags = list(rejected_tags_cursor)
                print(f"DEBUG REVISION_NOTES: Found {len(rejected_tags)} rejected tags for sentence {sentence_id}")
                
                # Get the project name
                project_name = "Unknown Project"
                if sentence.get('project_id'):
                    try:
                        project = projects_collection.find_one({"_id": ObjectId(sentence.get('project_id'))})
                        if project:
                            project_name = project.get('name', 'Unknown Project')
                    except Exception as e:
                        print(f"DEBUG REVISION_NOTES: Error fetching project: {e}")
                
                revision_note_data = {
                    "sentenceId": sentence_id,
                    "sentenceText": sentence.get('textContent', ''),
                    "projectName": project_name,
                    "rejectedTags": [tag.get('tag', '') for tag in rejected_tags],
                    "reviewerComment": note.get('revision_comment', ''),
                    "reviewer": note.get('reviewer_username', ''),
                    "rejectionDate": note.get('rejection_date').strftime('%Y-%m-%d %H:%M:%S') if note.get('rejection_date') else 'Unknown date'
                }
                
                revision_notes.append(revision_note_data)
                print(f"DEBUG REVISION_NOTES: Added revision note for sentence: {sentence_id}")
                
            except Exception as e:
                print(f"DEBUG REVISION_NOTES: Error processing note for sentence {sentence_id}: {e}")
                continue
        
        print(f"DEBUG REVISION_NOTES: Returning {len(revision_notes)} revision notes for user {username}")
        return jsonify(revision_notes), 200

    except Exception as e:
        print(f"DEBUG REVISION_NOTES: Error fetching revision notes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error during revision notes fetch"}), 500
       
@app.route('/api/annotator/acknowledge_revision', methods=['POST'])
@token_required
def acknowledge_revision():
    """
    Endpoint 5: Annotator Acknowledgment - Moves rejected sentence back to IN_PROGRESS.
    """
    try:
        data = request.get_json()
        sentence_id = data.get('sentence_id')
        annotator_username = request.current_user['username']
        
        if not sentence_id:
            return jsonify({"error": "Sentence ID is required"}), 400

        # 1. Update Sentence Table status back to IN_PROGRESS
        sentences_collection.update_one(
            {"_id": ObjectId(sentence_id), "username": annotator_username},
            {"$set": {
                "review_status": "IN_PROGRESS", 
                "submission_date": None, 
                "reviewed_by": None,
                "review_date": None
            }}
        )

        # 2. Mark the Revision Note as acknowledged/read
        revision_notes_collection.update_many(
            {"sentence_id": sentence_id, "annotator_username": annotator_username, "acknowledged": False},
            {"$set": {"acknowledged": True}}
        )
        
        # 3. Reset tags: Mark all staged tags for this sentence as Pending (allowing re-work)
        staged_tags_collection.update_many(
            {"source_sentence_id": sentence_id, "username": annotator_username, "review_status": "Rejected"},
            {"$set": {"review_status": "Pending", "review_comments": None}}
        )
        
        log_action_and_update_report(annotator_username, f"Acknowledged rejection and started re-work on sentence {sentence_id}.")
        
        return jsonify({"message": f"Sentence {sentence_id} ready for re-work."}), 200

    except Exception as e:
        print(f"Error acknowledging revision: {e}")
        return jsonify({"error": "Internal server error during acknowledgment"}), 500
    
@app.route('/stats', methods=["GET"])
def get_stats():
    try:
        username_arg = request.args.get('username')
        user = users_collection.find_one({"username": username_arg})
        if not user or user.get("role") != "admin":
            return jsonify({"message": "Unauthorized access"}), 403

        # 1. Calculate stats based on UNIQUE sentences across all projects.
        pipeline = [
            {"$group": {
                "_id": {
                    "project_id": "$project_id", 
                    "original_index": "$original_index"
                },
                "is_annotated_status": {"$max": "$is_annotated"},
                "unique_sentence_id": {"$first": "$_id"}
            }},
            {"$group": {
                "_id": None,
                "total_unique_sentences": {"$sum": 1},
                "total_annotated": {"$sum": {"$cond": ["$is_annotated_status", 1, 0]}}
            }}
        ]

        stats_result = list(sentences_collection.aggregate(pipeline))
        
        if stats_result:
            stats = stats_result[0]
            total_sentences = stats.get("total_unique_sentences", 0)
            annotated_sentences = stats.get("total_annotated", 0)
        else:
            total_sentences = 0
            annotated_sentences = 0

        non_annotated_sentences = total_sentences - annotated_sentences

        # 2. Sentences by User
        user_counts = {}
        for user in users_collection.find():
            user_name = user['username']
            count = sentences_collection.count_documents({"username": user_name})
            user_counts[user_name] = count

        return jsonify({
            "total_sentences": total_sentences,
            "annotated_sentences": annotated_sentences,
            "non_annotated_sentences": non_annotated_sentences,
            "user_counts": user_counts
        })
        
    except Exception as e:
        print(f"Error in stats endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)