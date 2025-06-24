# AI-Powered CV Generator Frontend

This document provides an overview of the AI-Powered CV Generator's frontend component. This web interface allows users to input their professional information, which is then used to automatically generate a polished CV in PDF format.

## Description

The frontend is a single-page application built with HTML, Tailwind CSS for styling, and vanilla JavaScript. It interacts with a Python Flask backend to handle data scraping, AI-powered content generation, and PDF creation.

The user provides URLs to their online profiles (like LinkedIn or GitHub), a target job description, and any other relevant details. The application then scrapes the content from the provided links, constructs a detailed prompt for an AI model, and generates a CV tailored to the job description. The user has the option to review and edit the generated prompt before the final CV is created.

## Technologies Used

The application is built with the following technologies:

* **Backend:**
    * Flask
    * requests
    * WeasyPrint
    * Markdown2
    * python-dotenv
    * gunicorn

* **Frontend:**
    * HTML
    * Tailwind CSS
    * JavaScript

## How to Use

To run this application, you will need a running backend that serves the required API endpoints.

1.  **Provide Information:**
    * In the "Info Links" section, add URLs to your online profiles (e.g., portfolio, GitHub, LinkedIn). You can specify the "scrape depth" for each link to control how much information is gathered.
    * Paste the target job description into the "Target Job Description" text area.
    * Add any other relevant information, such as certifications or additional projects, in the "Additional Details" section.

2.  **Select an AI Model:** Choose an available AI model from the dropdown menu. The application periodically checks the health of the backend services and populates this list.

3.  **Initiate the Process:** Click the "Start Process" button. The application will first scrape the provided URLs and then generate a prompt for the AI.

4.  **Review and Edit (Optional):** A modal window will appear displaying the generated prompt. You can review and edit this prompt to fine-tune the information sent to the AI. Click "Generate CV with this Prompt" to proceed.

5.  **View and Download:** The generated CV will appear in the "Generated CV" text area. You can then click the "Download PDF" button to save a copy of your new CV.