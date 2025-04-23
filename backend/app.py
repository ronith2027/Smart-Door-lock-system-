import sqlite3
import os
import matplotlib
matplotlib.use('Agg') # Use Agg backend for non-interactive plotting
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash # For potential future use
import requests # Added for Telegram API calls
import random
from datetime import datetime, timedelta
import matplotlib.dates as mdates # For formatting date axis
"""import requests"""
"""import os"""
"""from datetime import datetime"""
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user # Make sure current_user is available

# --- Placeholder Owner Data ---
OWNERS_DATA = {
    'owner1': {
        'id': 'owner1',
        'name': 'RAKSHITH MAHESH',
        'photo': 'owner1.png', # Ensure this file exists in backend/static/
        'details': {
            'Title': 'Primary Owner',
            'Contact': 'vijay@example-domain.com',
            'Access Level': 'Master',
            'Emergency Contact': '+1-555-0101',
            'Notes': 'Resides in Tower A, Apt 101.'
        }
    },
    'owner2': {
        'id': 'owner2',
        'name': 'RITHIK MADHAV V',
        'photo': 'owner2.jpg', # Ensure this file exists in backend/static/
        'details': {
            'Title': 'System Administrator',
            'Contact': 'nikitha.s@example-domain.com',
            'Access Level': 'Admin',
            'Department': 'IT Security',
            'Joined': '2022-05-20'
        }
    },
    'owner3': {
        'id': 'owner3',
        'name': 'RONITH H U',
        'photo': 'owner3.jpg', # Use a default image
        'details': {
            'Title': 'On-Site Security',
            'Contact': 'security@example-domain.com',
            'Access Level': 'Monitor / Limited Unlock',
            'Phone': '+1-555-0103',
            'Location': 'Main Lobby'
        }
    }
}
# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")
TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")

# Create static directory if it doesn't exist
os.makedirs(STATIC_FOLDER, exist_ok=True)

# --- Flask App Initialization ---
app = Flask(__name__,
            static_folder=STATIC_FOLDER,
            template_folder=TEMPLATE_FOLDER)
# IMPORTANT: Set a strong secret key, preferably via environment variable
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key_change_in_production')

# --- Database Initialization ---
def init_db():
    """Initializes the database, creating the access_log table if it doesn't exist."""
    conn = None
    try:
        print(f"Connecting to database at: {DATABASE}")
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        print("Checking/Creating database tables...")

        # --- Access Log Table ---
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='access_log'")
        if not cur.fetchone():
            print("Creating 'access_log' table...")
            cur.execute('''
                CREATE TABLE access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    confidence REAL NOT NULL
                )
            ''')
            print("'access_log' table created.")
        else:
            print("'access_log' table already exists.")

        # --- Chat Messages Table (REMOVED) ---
        # The local chat_messages table is no longer needed as we fetch from Telegram.
        # If the table exists from previous runs, it will just be ignored.

        conn.commit()
        print("Database initialization check complete.")

    except sqlite3.Error as e:
        print(f"Database error during initialization: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

# --- User Authentication ---
try:
    # Expects auth.py in the same directory with: users = {'username': 'password'}
    from auth import users
except ImportError:
    print("WARNING: auth.py not found or 'users' dictionary not defined. Using default user.")
    users = {'admin': 'password'} # Fallback - INSECURE, FOR DEV ONLY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

class User(UserMixin):
    """Basic User class for Flask-Login."""
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    """Loads user object for Flask-Login."""
    if user_id in users:
        return User(user_id)
    return None

# --- Standard Routes ---

@app.route('/', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        uname = request.form.get('username')
        pwd = request.form.get('password')

        if not uname or not pwd:
            flash('Username and password are required.', 'warning')
            return render_template('login.html')

        # IMPORTANT: Use password hashing (e.g., check_password_hash) in production!
        if uname in users and users[uname] == pwd: # Plain text check (INSECURE)
            user = User(uname)
            login_user(user)
            flash(f'Welcome back, {uname}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handles user logout."""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Displays the main dashboard with action buttons."""
    return render_template('dashboard.html', username=current_user.id)

# --- Simulation & Plotting Helpers ---

def generate_simulated_daily_data(day_offset=0, num_points=15):
    """Generates random timestamp/confidence data for a specific day offset from today."""
    now = datetime.now()
    target_date = (now - timedelta(days=day_offset)).date()
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    timestamps = []
    confidences = []

    # Ensure the last point is close to 'now' if it's today (day_offset=0)
    if day_offset == 0:
        # Add a point very close to the current time
        timestamps.append(now - timedelta(minutes=random.randint(1,5))) # Slightly before now
        confidences.append(random.randint(50, 200))
        num_points -= 1 # Decrement points needed

    # Generate other points randomly within the day
    day_seconds = 24 * 60 * 60
    for _ in range(num_points):
        random_seconds = random.randint(0, day_seconds - 1)
        timestamp = start_of_day + timedelta(seconds=random_seconds)
        # Avoid duplicates (simple check)
        if timestamp not in timestamps:
            timestamps.append(timestamp)
            confidences.append(random.randint(50, 200))

    # Sort data by timestamp
    sorted_data = sorted(zip(timestamps, confidences))
    timestamps = [item[0] for item in sorted_data]
    confidences = [item[1] for item in sorted_data]

    return timestamps, confidences

def plot_simulated_graph(timestamps, confidences, filename, title):
    """Creates and saves a plot using Matplotlib."""
    if not timestamps: # Handle case with no data
        print(f"Warning: No data provided for plot '{title}'. Skipping.")
        # Optionally create a placeholder image
        plt.figure(figsize=(7, 3))
        plt.text(0.5, 0.5, 'No Data Available', ha='center', va='center')
        plt.title(title)
        plt.xticks([])
        plt.yticks([])
    else:
        plt.figure(figsize=(7, 3)) # Smaller figure size for multiple graphs
        plt.plot(timestamps, confidences, marker='o', linestyle='-', markersize=4, color='#4a90e2') # Use a theme color
        plt.ylim(0, 250) # Set Y-axis limit slightly above max confidence
        plt.title(title)
        plt.ylabel("Confidence Level")
        plt.xlabel("Time")

        # Format the x-axis to show time nicely
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M')) # Show Hour:Minute
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=7)) # Auto ticks
        plt.gcf().autofmt_xdate() # Auto-rotate date labels

        plt.grid(True, linestyle='--', alpha=0.5, color='#555') # Subtle grid for dark theme
        plt.tight_layout()

        # Set dark theme background for the plot
        plt.style.use('dark_background')
        plt.rcParams.update({ # Override specific colors if needed
            "figure.facecolor":  "#2b2d31", # Match widget background
            "axes.facecolor":    "#3a3f44", # Plot area background
            "savefig.facecolor": "#2b2d31",
            "axes.edgecolor":    "#777",
            "axes.labelcolor":   "#ccc",
            "axes.titlecolor":   "#eee",
            "xtick.color":       "#aaa",
            "ytick.color":       "#aaa",
            "grid.color":        "#555",
            "text.color":        "#ccc",
        })

    # Ensure the static directory exists
    static_dir = os.path.join(BASE_DIR, "static")
    os.makedirs(static_dir, exist_ok=True)
    full_path = os.path.join(static_dir, filename)

    try:
        plt.savefig(full_path)
        print(f"Saved plot: {full_path}")
    except Exception as e:
        print(f"Error saving plot {full_path}: {e}")
    plt.close() # Close the figure to free memory
    return filename # Return just the filename for url_for


# --- Owner Log Selection Route ---
@app.route('/owner_log_select')
@login_required
def owner_log_select():
    """Displays links to view logs for each owner."""
    # We can reuse the OWNERS_DATA dictionary defined earlier
    # Make sure OWNERS_DATA is defined globally or accessible here
    owner_ids = list(OWNERS_DATA.keys()) # Get ['owner1', 'owner2', 'owner3']
    owner_names = {owner_id: OWNERS_DATA[owner_id]['name'] for owner_id in owner_ids}

    return render_template('owner_log_select.html',
                           owner_names=owner_names,
                           username=current_user.id)

# --- Owner Log View Route ---
@app.route('/owner_log_view/<owner_id>')
@login_required
def owner_log_view(owner_id):
    """Generates and displays 7 days of simulated log graphs for an owner."""
    owner_info = OWNERS_DATA.get(owner_id)
    if not owner_info:
        flash(f"Owner ID '{owner_id}' not found.", "warning")
        return redirect(url_for('owner_log_select'))

    owner_name = owner_info['name']
    graph_files = {} # Dictionary to store filenames for each day

    print(f"Generating graphs for {owner_name}...")
    for day_num in range(1, 8): # Generate for Day 1 to Day 7
        day_offset = 7 - day_num # Day 7 is offset 0, Day 1 is offset 6
        timestamps, confidences = generate_simulated_daily_data(day_offset=day_offset)

        # Create a unique filename for each plot
        plot_filename = f"{owner_id}_day{day_num}_{random.randint(1000,9999)}.png" # Add random int to help avoid caching
        plot_title = f"{owner_name} - Day {day_num} ({ (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d') })"
        if day_num == 7:
            plot_title += " (Latest)"

        # Generate and save the plot
        saved_filename = plot_simulated_graph(timestamps, confidences, plot_filename, plot_title)
        graph_files[f'day{day_num}'] = saved_filename # Store filename: day7: 'owner1_day7_1234.png'

    print(f"Finished generating graphs for {owner_name}.")
    return render_template('owner_log_view.html',
                           owner=owner_info, # Pass full owner info if needed
                           graph_files=graph_files, # Pass the dict of filenames
                           username=current_user.id)


@app.route('/api/record', methods=['POST'])
def record():
    """API endpoint to record access log events (called by external device)."""
    # Add security (API key, authentication) if this is exposed publicly
    timestamp = request.form.get('timestamp')
    confidence_str = request.form.get('confidence')

    if not timestamp or confidence_str is None:
        return 'Missing timestamp or confidence', 400
    try:
        confidence = float(confidence_str)
    except ValueError:
        return 'Invalid confidence value', 400

    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("INSERT INTO access_log (timestamp, confidence) VALUES (?, ?)", (timestamp, confidence))
        conn.commit()
        print(f"Recorded access: {timestamp}, {confidence}")
        return 'Recorded', 200
    except sqlite3.Error as e:
        print(f"Database error recording access: {e}")
        if conn: conn.rollback()
        return 'Database error', 500
    finally:
        if conn: conn.close()

# --- Telegram History Route ---

# --- Helper function to get Telegram file URL ---
def get_telegram_file_url(file_id, bot_token):
    """
    Calls Telegram's getFile API to get a downloadable URL for a file.
    Returns the full URL or None if an error occurs.
    """
    get_file_api_url = f"https://api.telegram.org/bot{bot_token}/getFile"
    params = {'file_id': file_id}
    try:
        response = requests.get(get_file_api_url, params=params, timeout=10) # Short timeout for this specific call
        response.raise_for_status()
        data = response.json()
        if data.get("ok"):
            file_path = data.get("result", {}).get("file_path")
            if file_path:
                # Construct the full download URL
                # Note: These URLs might expire after some time
                return f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
            else:
                print(f"Error: 'file_path' not found in getFile response for file_id {file_id}")
                return None
        else:
            print(f"Error: Telegram getFile API returned 'ok': false. Description: {data.get('description')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error calling getFile API for file_id {file_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in get_telegram_file_url for file_id {file_id}: {e}")
        return None

# --- Updated Telegram History Route ---

@app.route('/telegram_history')
@login_required
def telegram_history():
    """Fetches and displays chat history (text & photos) from the Telegram Bot API."""
    messages = []
    error_message = None

    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        error_message = "Configuration Error: TELEGRAM_BOT_TOKEN environment variable is not set."
        print(error_message)
        flash("Cannot fetch Telegram history: Bot token not configured.", "danger")
        return render_template('telegram_history.html', messages=messages, error=error_message)

    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {'timeout': 10, 'limit': 50} # Limit to 50 updates to reduce load time

    print("Fetching Telegram updates...") # Log start
    try:
        response = requests.get(telegram_api_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("ok"):
            updates = data.get("result", [])
            if not updates:
                error_message = "No recent messages found in Telegram history."
            else:
                print(f"DEBUG: Fetched {len(updates)} updates. Processing...")

            for update in updates:
                message = update.get("message") or update.get("edited_message")
                if message:
                    msg_data = {"type": "other", "content": "[Unsupported message type]"} # Default
                    sender_info = message.get("from", {})
                    timestamp_unix = message.get("date")
                    msg_text = message.get("text")
                    msg_photo_array = message.get("photo") # Check for photo array

                    # Construct sender name
                    sender_name = sender_info.get("first_name", "Unknown User")
                    if sender_info.get("last_name"):
                         sender_name += f" {sender_info['last_name']}"
                    msg_data["sender_name"] = sender_name

                    # Convert Unix timestamp
                    if timestamp_unix:
                        dt_object = datetime.fromtimestamp(timestamp_unix)
                        msg_data["timestamp"] = dt_object.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        msg_data["timestamp"] = "No date provided"

                    # --- Check message type ---
                    if msg_text:
                        msg_data["type"] = "text"
                        msg_data["content"] = msg_text
                        print(f"  Processing text message from {sender_name}")

                    elif msg_photo_array:
                        # Photo received! Get the highest resolution file_id
                        # Telegram sends multiple sizes, last one is usually largest
                        if msg_photo_array:
                            best_photo = msg_photo_array[-1] # Get the last element (often highest res)
                            file_id = best_photo.get("file_id")
                            print(f"  Processing photo message from {sender_name}, file_id: {file_id}")
                            if file_id:
                                # Make the *additional* API call to get the file URL
                                photo_url = get_telegram_file_url(file_id, bot_token)
                                if photo_url:
                                    msg_data["type"] = "image"
                                    msg_data["content"] = photo_url # Store the direct URL
                                    print(f"    -> Got photo URL: {photo_url[:50]}...") # Log success (truncated)
                                else:
                                    msg_data["type"] = "text" # Fallback to text if URL fetch fails
                                    msg_data["content"] = "[Error fetching photo]"
                                    print(f"    -> FAILED to get photo URL for file_id {file_id}")
                            else:
                                msg_data["type"] = "text" # Fallback
                                msg_data["content"] = "[Photo data incomplete]"
                        else:
                            msg_data["type"] = "text" # Fallback
                            msg_data["content"] = "[Empty photo array received]"

                    # else: keep default "[Unsupported message type]"

                    messages.append(msg_data)
            print("Finished processing updates.")

        else:
            api_error_desc = data.get('description', 'Unknown Telegram API error')
            error_message = f"Telegram API Error (getUpdates): {api_error_desc}"
            print(error_message)
            flash("Failed to retrieve messages from Telegram.", "danger")

    except requests.exceptions.Timeout:
        error_message = "Error: Request to Telegram API (getUpdates) timed out."
        print(error_message)
        flash(error_message, "warning")
    except requests.exceptions.RequestException as e:
        error_message = f"Network or API Connection Error (getUpdates): {e}"
        print(error_message)
        flash("Could not connect to Telegram API.", "danger")
    except Exception as e:
        error_message = f"An unexpected error occurred processing Telegram data: {e}"
        print(error_message) # Log the full traceback if needed
        flash("An internal error occurred.", "danger")

    return render_template('telegram_history.html', messages=messages, error=error_message)

# --- End Updated Telegram History Route ---

@app.route('/owner/<owner_id>')
@login_required
def owner_detail(owner_id):
    """Displays the detail page for a specific owner."""
    owner_info = OWNERS_DATA.get(owner_id) # Get data using the ID from the URL

    if not owner_info:
        # If owner_id doesn't match our data, show warning and redirect
        flash(f"Details for Owner ID '{owner_id}' not found.", "warning")
        return redirect(url_for('dashboard'))

    # If owner found, render the detail template, passing the owner's data
    return render_template('owner_detail.html',
                           owner=owner_info,
                           username=current_user.id) # Pass username for header

# --- End new route function ---


# --- Run Application ---
if __name__ == "__main__":
    print("--- Starting Door Access Dashboard Backend ---")
    init_db() # Ensure database exists on startup
    print(f"Flask app running on http://0.0.0.0:5000 (Debug: {app.debug})")
    print("Reminder: Ensure TELEGRAM_BOT_TOKEN environment variable is set.")
    # Set debug=False for production deployment!
    app.run(host='0.0.0.0', port=5000, debug=True)