# Computerised Student Attendance System - Android

This project is a Python/Kivy Android version of the school attendance system.

## Features

- Teacher login
- Mark Present, Absent and Late
- SQLite database
- Add and delete learners
- Search attendance
- Attendance summary
- CSV report export
- Mobile portrait interface

## Default login

Username: teacher
Password: 1234

## Build on GitHub from an Android phone

1. Create a GitHub account if you do not already have one.
2. Create a new repository.
3. Upload:
   - main.py
   - buildozer.spec
   - .github/workflows/build-apk.yml
4. Open the repository's Actions tab.
5. Select "Build Android APK".
6. Press "Run workflow".
7. Wait for the build to finish.
8. Open the completed workflow and download the artifact named:
   attendance-system-apk
9. Extract the artifact and install the APK on your Android phone.

Android may ask you to allow installation from the browser/file manager you used. Only install the APK you built from your own repository.
