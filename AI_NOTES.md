# AI Notes

This document explains how AI was used during the development of this project and what work was completed manually.

## 1. Which parts were AI-generated vs. written by me

AI-generated

AI (Claude) was used to generate the initial implementation of:

FastAPI application (src/main.py)
API endpoints
Data models
JSON file persistence logic
ExpenseStore class
Pytest test suite
Initial README
Initial AI Notes
Written or completed by me

I personally:

Reviewed the generated code.
Verified that every API endpoint worked correctly.
Tested the project from a clean checkout.
Ran the complete test suite.
Verified JSON persistence after server restart.
Organized the repository according to the assignment instructions.
Reviewed the documentation before submission.

## 2. What I validated, tested,

I did not submit the AI-generated code without verification.

I manually checked the following:

All API endpoints returned the expected responses.
Input validation correctly rejected invalid requests.
Expense deletion worked correctly.
Category filtering was case-insensitive.
Expense totals were calculated correctly.
JSON data persisted after restarting the server.
The complete pytest suite passed successfully.
Swagger documentation loaded correctly.

During testing, one issue related to a Pydantic date field was identified and corrected before final submission.

## 3. AI suggestions I decided not to use

The AI suggested several improvements that were intentionally not included because they were outside the assignment requirements:

Using SQLite instead of JSON storage.
Adding JWT authentication.
Adding user accounts.
Adding pagination.
Splitting the project into multiple modules and service layers.
Adding Docker support.
Adding CI/CD workflows.

These suggestions would improve a production application but would increase the project's complexity beyond the scope of the assignment, so I kept the implementation focused on the required functionality.


## Bonus Feature Implemented

-The project includes Swagger/OpenAPI documentation using FastAPI.

After starting the server, the interactive API documentation is available at:

http://127.0.0.1:8000/docs
