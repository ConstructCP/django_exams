# django_exams

A site where you can take exams provided you have exam question data.

Supported functionality:
* Taking exams
  * May choose number of questions
* Store exams history
* Login / Registration
* Upload exam data
* Application as docker container
* Menu bar with navigation

To-do list:
* Design - search for ready templates
* Show correct/incorrect answers on results page (graphically)
* Question tags
* Change DB to Postgres
* Django CLI command to upload exam data
* Create questions from UI
* Exam source field (from app or from user)
* Checking for duplicates during question upload
* Separate admin and user sites: no login for admin to app, no login for user to admin
* Add app admin user type