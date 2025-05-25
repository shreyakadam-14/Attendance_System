# Face Recognition Attendance System with Supabase

This is a real-time face attendance system built using Python, OpenCV, and `face_recognition`, integrated with Supabase for backend data storage and image management. The system identifies registered students, marks their attendance, and displays their information and image on screen.

## Table of Contents

-   [Features](#features)
-   [Prerequisites](#prerequisites)
-   [Supabase Setup](#supabase-setup)
    -   [Create Supabase Project](#1-create-supabase-project)
    -   [Database Schema](#2-database-schema)
    -   [Storage Bucket and Policies](#3-storage-bucket-and-policies)
    -   [Database Row Level Security (RLS)](#4-database-row-level-security-rls)
    -   [Get Supabase Credentials](#5-get-supabase-credentials)
-   [Local Setup](#local-setup)
    -   [Clone the Repository](#1-clone-the-repository)
    -   [Create Virtual Environment](#2-create-virtual-environment)
    -   [Install Dependencies](#3-install-dependencies)
    -   [Configure Environment Variables](#4-configure-environment-variables)
    -   [Prepare Resources](#5-prepare-resources)
-   [Usage](#usage)
    -   [1. Add Student Data to Supabase](#1-add-student-data-to-supabase)
    -   [2. Generate Face Encodings and Upload Images](#2-generate-face-encodings-and-upload-images)
    -   [3. Run the Attendance System](#3-run-the-attendance-system)
-   [Project Structure](#project-structure)
-   [Troubleshooting](#troubleshooting)
-   [Contributing](#contributing)
-   [License](#license)

## Features

* **Real-time Face Detection:** Utilizes `face_recognition` to detect faces from a webcam feed.
* **Student Recognition:** Compares detected faces against a database of known student encodings.
* **Supabase Backend:** Stores student data in a PostgreSQL database and student images in Supabase Storage.
* **Automated Attendance Marking:** Marks attendance for recognized students with a configurable cooldown period (e.g., 30 seconds).
* **Dynamic UI:** Displays student information (name, ID, major, attendance count) and their photo upon successful recognition.
* **Visual Feedback:** Provides "Loading..." text for image fetching and clear "Marked" status.
* **Modular Design:** Separate scripts for data addition, encoding generation, and the main attendance system.

## Prerequisites

Before you begin, ensure you have the following installed:

* **Python 3.x:** (Recommended 3.8+)
    * Download from [python.org](https://www.python.org/downloads/)
* **Git:** For cloning the repository.
    * Download from [git-scm.com](https://git-scm.com/downloads)
* **OpenCV Dependencies:** Face recognition relies on Dlib, which uses C++ features. You might need build tools:
    * **Windows:** Microsoft Visual C++ Build Tools (comes with Visual Studio Installer, select "Desktop development with C++" workload).
    * **macOS:** Xcode Command Line Tools (`xcode-select --install`).
    * **Linux:** `sudo apt-get update && sudo apt-get install build-essential cmake` (for Debian/Ubuntu based systems).

## Supabase Setup

This system heavily relies on Supabase for data management.

### 1. Create Supabase Project

1.  Go to [Supabase](https://supabase.com/).
2.  Sign up or Log in.
3.  Click "New project".
4.  Choose your organization and a suitable project name (e.g., `face-attendance-system`).
5.  Set a strong database password.
6.  Choose a region.
7.  Click "Create new project".

### 2. Database Schema

Once your project is created, you need to set up the `students` table.

1.  In your Supabase project dashboard, navigate to **Table Editor** (the spreadsheet icon on the left sidebar).
2.  Click `+ New table`.
3.  Configure the table with the following details:
    * **Name:** `students`
    * **Enable Row Level Security (RLS):** Keep this **checked** for now, we'll add policies later.
    * **Columns:**
        * `id`: `text`, `Primary Key`, `Is Unique` (This will store student IDs, e.g., "2004", "2005").
        * `name`: `text`
        * `major`: `text`
        * `starting_year`: `int4`
        * `total_attendance`: `int4`, default value `0`
        * `standing`: `text` (e.g., "G", "B", "W")
        * `year`: `int4` (Current academic year)
        * `last_attendance_time`: `timestamp with time zone`, default value `now()` (This will be updated every time attendance is marked).
4.  Click "Save".

### 3. Storage Bucket and Policies

You'll need a storage bucket to store student images.

1.  In your Supabase project dashboard, navigate to **Storage** (the bucket icon on the left sidebar).
2.  Click `+ New bucket`.
3.  **Name:** `images`
4.  **Public bucket:** Keep this **unchecked** (we'll use RLS policies to manage access).
5.  Click "Create bucket".

Now, set up Row Level Security (RLS) policies for the `images` bucket to allow your application to upload and download images:

1.  After creating the `images` bucket, click on it.
2.  Go to the **Policies** tab.
3.  **To allow uploads (for `EncodeGenerator.py`):**
    * Click "New policy".
    * Choose "Custom policy".
    * **Name:** `Allow public uploads to images bucket`
    * **Permissions:** `INSERT` (Only check INSERT)
    * **Target Roles:** `anon` (Add this role)
    * **Using a `WITH CHECK` expression:** `bucket_id = 'images'`
    * Click "Review" and then "Save policy".
4.  **To allow downloads (for `Main.py`):**
    * Click "New policy".
    * Choose "Custom policy".
    * **Name:** `Allow public read access to images bucket`
    * **Permissions:** `SELECT` (Only check SELECT)
    * **Target Roles:** `anon` (Add this role)
    * **Using a `USING` expression:** `bucket_id = 'images'`
    * Click "Review" and then "Save policy".

### 4. Database Row Level Security (RLS)

Although you checked RLS when creating the `students` table, you need to define policies to allow your application to interact with it.

1.  In your Supabase project dashboard, navigate to **Authentication** > **Policies**.
2.  Select the `public` schema and then the `students` table.
3.  **For `INSERT` (used by `AddDatatoDatabase.py`):**
    * Click "New policy".
    * Select "Custom policy".
    * **Name:** `Allow public inserts to students`
    * **Permissions:** `INSERT`
    * **Target Roles:** `anon`
    * **Using a `WITH CHECK` expression:** `true` (This allows any insert for anon users, you can refine this later if needed)
    * Click "Review" and "Save policy".
4.  **For `SELECT` (used by `Main.py` to fetch student data):**
    * Click "New policy".
    * Select "Custom policy".
    * **Name:** `Allow public select to students`
    * **Permissions:** `SELECT`
    * **Target Roles:** `anon`
    * **Using a `USING` expression:** `true`
    * Click "Review" and "Save policy".
5.  **For `UPDATE` (used by `Main.py` to mark attendance):**
    * Click "New policy".
    * Select "Custom policy".
    * **Name:** `Allow public update to students`
    * **Permissions:** `UPDATE`
    * **Target Roles:** `anon`
    * **Using a `USING` expression:** `true`
    * Click "Review" and "Save policy".

### 5. Get Supabase Credentials

You'll need your Supabase Project URL and Public Anon Key.

1.  In your Supabase project dashboard, navigate to **Project Settings** (the cog icon on the left sidebar).
2.  Go to **API**.
3.  Copy your **Project URL**.
4.  Copy your **anon (public)** `public` key.
