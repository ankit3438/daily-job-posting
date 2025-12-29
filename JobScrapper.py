import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv

load_dotenv()
from dotenv import load_dotenv

load_dotenv()

class JobScraper:
    def __init__(self):
        self.jobs = []
        self.search_query = "java backend developer 3 years experience"
        
    def search_jobs_serper(self):
        """Search jobs using Serper API (Google Search API) for India - last 24 hours"""
        api_key = os.environ.get('SERPER_API_KEY')
        
        if not api_key:
            print("Warning: SERPER_API_KEY not found, skipping Serper search")
            return []
        
        url = "https://google.serper.dev/search"
        payload = {
            "q": f"{self.search_query} india",
            "num": 20,
            "gl": "in",  # India location
            "hl": "en",  # English language
            "tbs": "qdr:d"  # Last 24 hours (d=day, w=week, m=month)
        }
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            results = response.json()
            
            jobs = []
            for item in results.get('organic', []):
                job = {
                    'title': item.get('title', 'N/A'),
                    'link': item.get('link', 'N/A'),
                    'snippet': item.get('snippet', 'N/A'),
                    'source': 'Google Search'
                }
                jobs.append(job)
            
            return jobs
        except Exception as e:
            print(f"Error with Serper API: {e}")
            return []
    
    def filter_by_experience(self, jobs):
        """Filter jobs based on 3 years experience requirement"""
        filtered = []
        experience_keywords = ['3 years', '2-4 years', '2-3 years', '3-5 years', 
                              'mid level', 'intermediate', 'junior']
        
        for job in jobs:
            text = (job.get('title', '') + ' ' + 
                   job.get('snippet', '') + ' ' + 
                   job.get('company', '')).lower()
            
            # Check if job mentions relevant experience level
            if any(keyword in text for keyword in experience_keywords):
                filtered.append(job)
            # If no experience mentioned, include it (might be suitable)
            elif not any(year in text for year in ['5 years', '6 years', '7 years', '8 years', 
                                                    'senior', '10 years', '5+ years']):
                filtered.append(job)
        
        return filtered if filtered else jobs  # Return all if filtering removes everything
    
    def scrape_all(self):
        """Run Google search via Serper API"""
        print("Starting job search from Google Search (India)...")
        
        # Search using Serper
        serper_jobs = self.search_jobs_serper()
        
        # Use only Google results
        self.jobs = self.filter_by_experience(serper_jobs)
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_jobs = []
        for job in self.jobs:
            title_lower = job.get('title', '').lower()
            if title_lower not in seen_titles and title_lower != 'n/a':
                seen_titles.add(title_lower)
                unique_jobs.append(job)
        
        self.jobs = unique_jobs
        print(f"Found {len(self.jobs)} unique jobs from Google Search")
        return self.jobs
    
    def format_email_body(self):
        """Format jobs into HTML email with separate URLs and titles"""
        if not self.jobs:
            return "<p>No new jobs found matching your criteria.</p>"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .job {{ 
                    border: 1px solid #ddd; 
                    padding: 15px; 
                    margin: 10px 0; 
                    border-radius: 5px;
                    background-color: #f9f9f9;
                }}
                .job-title {{ 
                    color: #2557a7; 
                    font-size: 18px; 
                    font-weight: bold;
                    margin-bottom: 8px;
                }}
                .job-url {{
                    color: #0066cc;
                    margin: 10px 0;
                    word-break: break-all;
                }}
                .apply-link {{ 
                    display: inline-block;
                    background-color: #2557a7; 
                    color: white; 
                    padding: 8px 16px; 
                    text-decoration: none; 
                    border-radius: 4px;
                    margin-top: 10px;
                }}
                .source {{ 
                    color: #888; 
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <h2>Java Backend Developer Jobs - Posted in Last 24 Hours (India)</h2>
            <p>Found {len(self.jobs)} jobs on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        for i, job in enumerate(self.jobs, 1):
            html += f"""
            <div class="job">
                <div class="job-title">{i}. {job.get('title', 'N/A')}</div>
                <div class="job-url"><strong>URL:</strong> <a href="{job.get('link', '#')}">{job.get('link', 'N/A')}</a></div>
                <div class="job-url"><strong>Direct Link:</strong> {job.get('link', 'N/A')}</div>
                <a href="{job.get('link', '#')}" class="apply-link">Open Link</a>
                <div class="source">Source: {job.get('source', 'N/A')}</div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        return html
    
    def send_email(self):
        """Send email with job listings"""
        sender_email = os.environ.get('SENDER_EMAIL')
        sender_password = os.environ.get('SENDER_PASSWORD')
        receiver_email = os.environ.get('RECEIVER_EMAIL')
        
        if not all([sender_email, sender_password, receiver_email]):
            print("Error: Email credentials not configured")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Java Backend Jobs - {datetime.now().strftime("%Y-%m-%d")}'
        msg['From'] = sender_email
        msg['To'] = receiver_email
        
        html_body = self.format_email_body()
        msg.attach(MIMEText(html_body, 'html'))
        
        try:
            # Use Gmail SMTP with TLS
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print(f"Email sent successfully to {receiver_email}")
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

def main():
    scraper = JobScraper()
    scraper.scrape_all()
    scraper.send_email()

if __name__ == "__main__":
    main()