# Smart Roster Management System

## 1. Project Overview

The Smart Roster Management System is a web-based application developed using Python, Streamlit, and SQLite.

The main purpose of this application is to simplify employee scheduling and monthly roster management. It helps organizations manage employees, brands, processes, pods, assignments, leaves, holidays, and employee schedules.

The application also helps identify roster conflicts and makes scheduling easier.

## 2. Technologies Used

- Python
- Streamlit
- SQLite
- Pandas
- Git and GitHub

## 3. Main Features

- Dashboard for viewing roster information.
- Employee Management (Add, View, Edit, Delete).
- Pod Management.
- Brand Management.
- Process Management.
- Employee and Brand Assignments.
- Sample Data with 30 fictional employees.
- Automatic Monthly Roster Generation.
- Leave Management.
- Public Holiday Management.
- Roster Conflict Detection.
- CSV Export.

## 4. Project Links

**Live Application:**  
https://smart-roster-management-vghwxtamahzzyqtsfybccf.streamlit.app/

**GitHub Repository:**  
https://github.com/thusharshetty1906-a11y/smart-roster-management

## 5. Installation and Setup

### Step 1: Clone the repository

```bash
git clone https://github.com/thusharshetty1906-a11y/smart-roster-management.git
```

### Step 2: Open the project folder

```bash
cd smart-roster-management
```

### Step 3: Install required libraries

```bash
pip install -r requirements.txt
```

### Step 4: Run the application

```bash
streamlit run app.py
```

The application will open in your browser.

## 6. Database Structure

The application uses SQLite to store information.

The main database tables include:

- Employees
- Pods
- Brands
- Processes
- Assignments
- Leaves
- Roster
- Holidays

These tables help maintain relationships between employees, brands, processes, pods, and schedules.

## 7. Approach and Design Decisions

The system uses a database-driven approach to manage employee information and scheduling.

SQLite was selected because it is lightweight and suitable for this project.

Streamlit was used to create a simple web interface, while Python handles the application logic.

The roster generation process uses employee assignments, leave information, holidays, and available scheduling settings.

Conflict detection helps identify scheduling problems so they can be reviewed and corrected.

## 8. Answers to Assessment Questions

### Q1. How are employees, brands, processes, pods, and their relationships modelled?

Employees, brands, processes, and pods are maintained as separate records in the database.

Employee and brand assignments are stored in the Assignments table. This helps connect employees with the brands and processes they are responsible for.

This structure makes it easier to manage employee responsibilities and update assignments when required.

### Q2. How does the roster generation process work?

The user selects a month and provides the available scheduling settings.

The application uses employee assignments, weekly off settings, leave information, and public holidays while generating the monthly roster.

The generated roster can be viewed in the application and exported as a CSV file.

### Q3. How do you handle single-resource and multi-employee brands?

The assignment structure allows one employee to be connected to a brand or multiple employees to share responsibilities for a brand.

For single-employee brands, the assigned employee handles the required work.

For multi-employee brands, the available assigned employees can be considered during scheduling.

### Q4. What happens if an employee responsible for all processes of a brand is unavailable?

The employee's approved leave or unavailable status is considered during roster generation.

If no other employee is assigned to handle the required work, the brand may have a staffing gap.

Such situations should be reviewed and resolved by assigning another suitable employee.

### Q5. How does the system handle conflicting requirements and insufficient staffing?

The application includes a Roster Conflict Detection section.

It identifies issues such as:

- Employees assigned during approved leave.
- Employees assigned on public holidays.
- Duplicate roster entries for the same employee and date.

These conflicts can be reviewed by the administrator.

If there is insufficient staffing, additional employee assignments may be required.

### Q6. Which parts are automated and which require human control?

**Automated tasks:**

- Monthly roster generation.
- Employee and assignment data management.
- Leave and holiday tracking.
- Roster conflict detection.
- CSV export.

**Human-controlled tasks:**

- Adding and updating employee information.
- Assigning employees to brands and processes.
- Approving leave information.
- Reviewing conflicts.
- Making final scheduling decisions.

Human control is important because administrators need to check business requirements before finalizing a roster.

### Q7. How would the system scale if the number of employees and brands doubled?

The system can be improved to support more employees and brands by optimizing database queries and improving the scheduling logic.

A larger database system can be introduced when the application grows.

The application can also be enhanced with user roles, access control, and better reporting features.

### Q8. If you had one extra week, what would you improve first?

I would first improve the roster scheduling algorithm to support more advanced business rules.

I would also add minimum staffing requirements, different operating calendars for brands and processes, and better coverage-gap detection.

I would improve manual roster editing and validation so administrators can understand the impact of schedule changes before finalizing them.

## 9. Future Enhancements

- Advanced employee scheduling rules.
- Minimum staffing and coverage management.
- Brand-specific and process-specific operating calendars.
- Improved roster editing and validation.
- Employee availability preferences.
- User authentication and role-based access.
- Advanced reports and analytics.

## 10. Conclusion

The Smart Roster Management System provides a simple way to manage employees, assignments, leaves, holidays, and monthly rosters.

It reduces manual scheduling work and helps administrators identify roster conflicts.

The project can be further improved by adding advanced scheduling rules and staffing coverage management.