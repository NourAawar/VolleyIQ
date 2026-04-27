# **VolleyIQ: Volleyball Tournament Management System**

VolleyIQ is a Django-based web platform for managing volleyball tournaments, teams, players, and matches. It features role-based access control for Club Managers, Coaches, and Players.


## Prerequisites


+	Docker Desktop installed and running
+ Run the app
  
git clone https://github.com/NourAawar/VolleyIQ.git

cd VolleyIQ

docker-compose up --build

Then open http://localhost:8000 in your browser.
Demo users and all data are loaded automatically on first run. Running docker-compose up again is safe. It skips the data load if users already exist.

________________________________________
## **Demo Accounts:**
Role	                  Username	                    Password

Club Manager	          manager1                     	dummypassword1

Coach                  	coach1	                      dummypassword1

Player	                MayaBechara                   dummypassword1

Player                	JudyNajjar	                  dummypassword1

Player                	LamaKhalil	                  dummypassword1

Player	                RitaChams	                    dummypassword1

________________________________________
## Roles & Access
**Club Manager:**

+	Create, edit, and delete tournaments and teams
+	Register teams in tournaments and generate match schedules (Round Robin, Single Elimination, Double Elimination)
+	Assign coaches to teams
+	Create player accounts and add/remove players from rosters
+	View all players in the system
+	Update match times and venues
+	Send system-wide announcements
+	View player availability across all matches

**Coach:**
+ Enter match scores for their team's matches
+ View and manage their team's match schedule
+ Assign tasks to players and track task completion
+ View team performance statistics and trends
+ Record player attendance at matches
+ View and update player availability
+ Send messages to their team
**Player:**
+	View upcoming matches and next match details
+	Report availability for matches
+	View and update assigned tasks
+	View personal performance statistics
+	View team announcements and coach messages
________________________________________
## Features

+ Tournament formats: Round Robin, Single Elimination (with bye seeding), Double Elimination (winners/losers brackets + grand final)
+ Standings: Live standings with wins, losses, points, and point differential
+ Performance stats: Per-player and per-team stats (kills, assists, blocks, digs, aces, errors) filterable by set period
+ Notifications: In-app notifications for score updates, venue changes, schedule generation, task assignments, and announcements
+ Attendance & availability tracking per match
+ Task management: Coaches assign tasks to players with due dates and status tracking
________________________________________
## Running Locally without Docker

pip install -r requirements.txt

python manage.py migrate

python manage.py loaddata fixtures/initial_data.json

python manage.py runserver
________________________________________
## Tech Stack
+ Backend: Django 6.0 (Python 3.12)
+ Database: SQLite
+ Frontend: Django templates with custom CSS
+ Containerization: Docker + Docker Compose
________________________________________

