# Smart Roster Management System

## Project Overview

The Smart Roster Management System is a web-based application developed using Python and Streamlit. It helps manage employees, teams, brands, processes, work schedules, leaves and public holidays.

The application also generates monthly employee rosters and identifies scheduling conflicts.

## Features

- Dashboard to view system information.
- Employee Management – Add, view, edit and delete employees.
- Pod Management – Manage teams and pod leads.
- Brand Management – Manage brands.
- Process Management – Manage business processes.
- Employee–Brand Assignments – Assign employees to brands and processes.
- Sample Data – Generate sample employees and assignments.
- Monthly Roster Generation – Generate employee work schedules.
- Leave Management – Manage employee leaves.
- Public Holiday Management – Add and manage holidays.
- Roster Conflict Detection – Identify scheduling conflicts and duplicate records.
- CSV Export – Download roster information.

## Technologies Used

- Python
- Streamlit
- SQLite
- Pandas

## Installation and Setup

1. Clone or download the project.
2. Open the project folder in VS Code.
3. Install the required libraries:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
streamlit run app.py
```

5. Open the local URL displayed in the terminal.

## Database

SQLite is used to store employee details, pods, brands, processes, assignments, leaves, public holidays and roster information.

## Project Purpose

The purpose of this project is to simplify employee scheduling and operations management through a single application.