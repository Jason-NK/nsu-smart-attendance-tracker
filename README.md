# NSU Smart Attendance Tracker

## Project Description
The NSU Smart Attendance Tracker is a web-based attendance system built for Norfolk State University students, professors, academic advisors, and IT support admins. Taking attendance by hand wastes class time and leads to missing or messed up records. Our system lets professors start a class session that displays a dynamic TOTP QR code on the screen, and students can scan the code with their phones (or enter the 6-digit backup code) to check into class in under 5 seconds.

## Team Members (Team: Trust The Process)
* **Tyson Corprew** - Project Coordinator / Design & UML Lead / Presentation Demo Lead
* **Carissa Cuffee** - Requirements Lead / Documentation Lead
* **Jason Kennedy** - Implementation Lead / Database Lead / Testing Lead

## Repository Link
https://github.com/Jason-NK/nsu-smart-attendance-tracker

## Major Features
* **Secure User Login:** Role-based login using official NSU emails (`@spartans.nsu.edu` or `@nsu.edu`) and `bcrypt` hashed passwords.
* **Role & Session Security:** Server-side role filter blocks students from professor routes, restricts students to their own history, and logs users out after 20 minutes of inactivity.
* **Course & Roster Management:** Professors can create courses and upload CSV class rosters (`.csv` only, under 2 MB).
* **Dynamic TOTP QR Code Sessions:** Professors can start and end attendance sessions with a dynamic TOTP QR code that refreshes every 30 seconds and automatically expires after the class end time.
* **Fast Student Check-In:** Students scan the live QR code or type the active 6-digit backup code along with their 7-digit NSU Student ID and receive a confirmation message right away.
* **Attendance Views & CSV Export:** Students can view their own attendance history, and professors can view class attendance tables and download CSV reports for grading.
* **Security Logging:** Records failed logins, expired QR scans, and unauthorized route attempts in `security_logs`.

## Technologies Used
* **Backend:** Python 3.11+ (Flask following MVC architecture)
* **Frontend:** HTML5, CSS3, JavaScript (Mobile and Desktop Web Views)
* **Database:** SQLite (`attendance.db`)
* **Security & QR Libraries:** PyOTP, qrcode, bcrypt, python-dotenv
* **Testing & Version Control:** pytest, Git, GitHub

## Setup and Installation Instructions
1. Clone or unzip the repository and open a terminal in the root folder:
   ```bash
   git clone https://github.com/Jason-NK/nsu-smart-attendance-tracker.git
   cd nsu-smart-attendance-tracker
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root folder (you can copy `.env.example`):
   ```bash
   cp .env.example .env
   ```
5. Set up the local SQLite database with the schema and seed accounts:
   ```bash
   sqlite3 attendance.db < database/schema.sql
   sqlite3 attendance.db < database/seed_data.sql
   ```
   *(If you are on Windows without the `sqlite3` command installed, run `python database/init_db.py` instead.)*

## How to Run the Project
1. Start the local web server from the root project folder:
   ```bash
   python src/app.py
   ```
2. Open your web browser and go to:
   `http://localhost:5000`
3. Sample test accounts:
   * **Student:** `jkennedy@spartans.nsu.edu` / Password: `Spartan123` (Student ID: `1234567`)
   * **Student 2:** `ccuffee@spartans.nsu.edu` / Password: `Spartan123` (Student ID: `7654321`)
   * **Professor:** `dnwosu@nsu.edu` / Password: `Professor123`
   * **IT Admin:** `itadmin@nsu.edu` / Password: `AdminPass123`
4. To run the automated test suite:
   ```bash
   pytest tests/
   ```

## Known Limitations
* Live camera QR scanning on a desktop computer requires a webcam; otherwise type the 6-digit backup TOTP code shown on the professor screen.
* Direct integration with Norfolk State University's official Canvas and Banner databases is out of scope for this semester, so rosters and exports use `.csv` files.
* The Academic Advisor dashboard view is saved for a future enhancement release.
