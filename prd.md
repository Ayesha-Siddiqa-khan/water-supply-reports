# 📄 Product Requirements Document (PRD)

## 1. Product Overview

**Product Name:** Simple Data App  
**Platform:** Desktop (Flask - Localhost)  

**Description:**  
A lightweight desktop app that allows users to upload multiple CSV/Excel files, merge them, and perform basic calculations like total sums and monthly breakdowns — without using any AI or external APIs.

---

## 2. Goal

- Provide a simple tool for combining and analyzing data  
- Avoid AI to reduce cost (0 token usage)  
- Keep the system fast, offline, and easy to use  

---

## 3. Core Features

### 3.1 File Upload
- Upload multiple files:
  - CSV
  - Excel (.xlsx)

---

### 3.2 Data Processing
- Read all uploaded files  
- Merge into one dataset  
- Normalize column names (lowercase)

---

### 3.3 Basic Calculations

#### Total Calculation
- If column `amount` exists:
  - Calculate total sum  

#### Monthly Breakdown
- If column `date` exists:
  - Group data by month  
  - Show sum per month  

---

### 3.4 Results Display
- Show:
  - Total amount  
  - Month-wise breakdown (list format)

---

## 4. User Flow

1. User opens app (localhost)  
2. Uploads multiple files  
3. Clicks submit  
4. App processes data  
5. Results displayed:
   - Total  
   - Monthly breakdown  

---

## 5. Technical Stack

- **Backend:** Flask (Python)  
- **Processing:** Pandas  
- **Frontend:** HTML (basic template)  
- **Storage:** Local files  

---

## 6. Data Rules

- Column names converted to lowercase  
- Required columns:
  - `amount` → for totals  
  - `date` → for monthly breakdown  

---

## 7. MVP Scope

### Include:
- File upload  
- Data merge  
- Total calculation  
- Monthly breakdown  

### Exclude:
- AI features  
- User login  
- Charts  
- Database  

---

## 8. Constraints

- Must work offline  
- Must be fast and lightweight  
- No external API usage  

---

## 9. Success Criteria

- Files upload successfully  
- Data merges correctly  
- Accurate totals and monthly results  

---
That sounds great! So, just to clarify the steps, you want the app to generate multiple outputs: a PDF report, an Excel file, a semi-structured file (like maybe a summary text), and a CSV file. Plus, the PDF needs to be visually appealing—colorful, bold, and organized in a table.

Would you like me to outline how you could structure that functionality in your app (e.g., using libraries like ReportLab for PDF, Pandas for Excel/CSV)? Or would you prefer a sample code snippet to generate one of these outputs?



---