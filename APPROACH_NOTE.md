# Approach Note – Smart Roster Management System

## 1. Introduction

The Smart Roster Management System is designed to simplify employee scheduling and monthly roster management. The main objective is to reduce manual scheduling work and help administrators manage employees, brands, processes, pods, leaves, holidays, and work assignments.

## 2. Problem Statement

Managing employee schedules manually can be difficult when employees work across different brands and processes. Employee leave, weekly offs, and public holidays can also create scheduling conflicts.

This project provides a centralized application to manage employee information, generate monthly rosters, and identify scheduling conflicts.

## 3. Proposed Solution

We developed a web-based application using Python and Streamlit.

The system provides:
- Employee, brand, process, and pod management.
- Employee and brand assignment management.
- Monthly roster generation.
- Leave and public holiday management.
- Roster conflict detection.
- CSV export for generated rosters.

## 4. Technology Stack

- **Python:** Application logic and scheduling operations.
- **Streamlit:** Web-based user interface.
- **SQLite:** Database for storing application information.
- **Pandas:** Data handling and processing.
- **Git and GitHub:** Source code management and version control.
- **Streamlit Community Cloud:** Application deployment.

## 5. System Architecture

The application follows a simple three-part structure:

1. **User Interface:** Streamlit provides the interface for administrators.
2. **Application Logic:** Python handles employee management, roster generation, leave management, and conflict detection.
3. **Database Layer:** SQLite stores employee, brand, process, pod, assignment, leave, holiday, and roster information.

## 6. Key Design Decisions

- SQLite was selected because it is lightweight and suitable for the current project.
- Streamlit was selected to build the application quickly with Python.
- Separate database tables are used to organize employees, brands, processes, and pods.
- Employee assignments are maintained separately to support multiple responsibilities.
- Conflict detection is included to help administrators identify scheduling problems.
- CSV export allows administrators to use roster information outside the application.

## 7. Limitations and Future Improvements

The current application provides basic roster generation and conflict detection.

Future improvements can include:
- Brand-specific and process-specific working calendars.
- Minimum staffing requirements.
- Advanced employee availability management.
- Better detection of staffing and coverage gaps.
- Manual roster editing with impact validation.
- Role-based access and administrator authentication.

## 8. Conclusion

The Smart Roster Management System provides a centralized solution for managing employee information and monthly schedules. It reduces manual work and helps administrators identify scheduling conflicts.

The system can be extended with advanced scheduling rules to support more complex business requirements.