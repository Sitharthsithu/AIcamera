import os
from flask import Flask, request, jsonify, render_template
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask_cors import CORS
from cryptography.fernet import Fernet
import json

app = Flask(__name__)
CORS(app)

# URLs for both spreadsheets
PHONE_SHEET_URL = "https://docs.google.com/spreadsheets/d/17i3oSiUn3-Mbd2M3mvkUXrwYx7aQc2dp-JvF2MJRydU/edit?usp=sharing"
ATTENDANCE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1LDWvYyDi34CCekcvsYOrOdrOphzLQN_35oZS9_H5wC4/edit?usp=sharing"

def extract_sheet_id(url):
    """Extract the Google Sheet ID from the URL"""
    try:
        parts = url.split('/')
        return parts[5]  # The ID is always the 6th part in a sharing URL
    except:
        return None

def get_spreadsheet_connection():
    """Setup connection to Google Sheets"""
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Try to use encrypted credentials first
        try:
            # Load encryption key
            with open('encryption.key', 'rb') as key_file:
                key = key_file.read()
            f = Fernet(key)
            
            # Load and decrypt credentials
            with open('service-account.encrypted', 'rb') as cred_file:
                encrypted_creds = cred_file.read()
            decrypted_creds = f.decrypt(encrypted_creds)
            
            # Use decrypted credentials
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                json.loads(decrypted_creds.decode()),
                scope
            )
            print("Using encrypted credentials")
            
        except FileNotFoundError as e:
            print(f"Encryption files missing: {str(e)}")
            print("Attempting to use direct credential file...")
            
            if not os.path.exists('credential.json'):
                raise FileNotFoundError("Neither encrypted credentials nor credential.json found")
                
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                'credential.json', scope)
            print("Using direct credential file")
        
        return gspread.authorize(credentials)
    except Exception as e:
        print(f"Error connecting to Google Sheets: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('app1.html')

@app.route('/api/search', methods=['GET'])
def search_attendance():
    try:
        # Get search phone number from query parameter
        search_phone = request.args.get('phone', '').strip()
        print(f"Searching for phone number: {search_phone}")
        
        if not search_phone:
            return jsonify({'status': 'error', 'message': 'Please provide a phone number'})
        
        # Connect to Google Sheets
        print("Connecting to Google Sheets...")
        gc = get_spreadsheet_connection()
        print("Successfully connected to Google Sheets")
        
        # Open the phone number spreadsheet
        print("Accessing phone sheet...")
        phone_sheet_id = extract_sheet_id(PHONE_SHEET_URL)
        print(f"Phone sheet ID: {phone_sheet_id}")
        phone_spreadsheet = gc.open_by_key(phone_sheet_id)
        phone_worksheet = phone_spreadsheet.sheet1
        print("Successfully accessed phone sheet")
        
        # Open the attendance spreadsheet
        attendance_sheet_id = extract_sheet_id(ATTENDANCE_SHEET_URL)
        attendance_spreadsheet = gc.open_by_key(attendance_sheet_id)
        attendance_worksheet = attendance_spreadsheet.sheet1
        
        # Get all records from phone sheet
        phone_records = phone_worksheet.get_all_records()
        phone_df = pd.DataFrame(phone_records)
        
        # Check if required columns exist in phone sheet
        phone_required_columns = ['Phone number', 'Name']
        missing_phone_columns = [col for col in phone_required_columns if col not in phone_df.columns]
        
        if missing_phone_columns:
            return jsonify({
                'status': 'error', 
                'message': f"Required columns missing in phone sheet: {', '.join(missing_phone_columns)}"
            })
        
        # Find name by phone number
        phone_match = phone_df[phone_df['Phone number'].astype(str) == search_phone]
        
        if phone_match.empty:
            return jsonify({
                'status': 'error', 
                'message': f"No name found for phone number '{search_phone}'."
            })
        
        # Get the name
        search_name = phone_match.iloc[0]['Name'].lower()
        display_name = phone_match.iloc[0]['Name']  # Original case for display
        
        # Get attendance records
        attendance_records = attendance_worksheet.get_all_records()
        attendance_df = pd.DataFrame(attendance_records)
        
        # Check if required columns exist in attendance sheet
        attendance_required_columns = ['Name', 'Timestamp', 'Course']
        missing_attendance_columns = [col for col in attendance_required_columns if col not in attendance_df.columns]
        
        if missing_attendance_columns:
            return jsonify({
                'status': 'error', 
                'message': f"Required columns missing in attendance sheet: {', '.join(missing_attendance_columns)}"
            })
        
        # Convert all names to lowercase for case-insensitive search
        attendance_df['Name'] = attendance_df['Name'].str.lower()
        
        # Filter by name (exact match)
        results = attendance_df[attendance_df['Name'] == search_name]
        
        if results.empty:
            return jsonify({
                'status': 'error', 
                'message': f"No attendance records found for '{display_name}'."
            })
        
        # Format results for JSON response
        formatted_results = []
        for _, row in results.iterrows():
            formatted_results.append({
                'name': display_name,
                'phone': search_phone,
                'timestamp': row['Timestamp'],
                'course': row['Course']
            })
        
        return jsonify({
            'status': 'success',
            'name': display_name,
            'phone': search_phone,
            'count': len(formatted_results),
            'results': formatted_results
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)