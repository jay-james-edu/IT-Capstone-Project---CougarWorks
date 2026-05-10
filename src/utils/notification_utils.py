"""
Notification and email utilities for CougarWorks.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications to users."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@cougarworks.edu')
        self.from_name = os.getenv('FROM_NAME', 'CougarWorks')
        self._initialized = True

    def is_configured(self):
        """Check if email service is properly configured."""
        return bool(self.smtp_username and self.smtp_password)

    def send_email(self, to_email, subject, body_html, body_text=None):
        """
        Send an email notification.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            body_html: HTML content of the email
            body_text: Plain text content (optional)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("Email service not configured. Set SMTP_USERNAME and SMTP_PASSWORD.")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add plain text version
            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))
            else:
                import re
                clean_text = re.sub('<[^<]+?>', '', body_html)
                msg.attach(MIMEText(clean_text, 'plain'))

            # Add HTML version
            msg.attach(MIMEText(body_html, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_grade_notification(self, student_email, student_name, course_name, grade):
        """Send a grade update notification."""
        subject = f"Grade Posted: {course_name}"

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f7fb; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #003359 0%, #002240 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .grade-box {{ background: #f9fafb; border-left: 4px solid #C60C30; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .grade {{ font-size: 36px; font-weight: bold; color: #003359; }}
                .footer {{ background: #f4f7fb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 CougarWorks</h1>
                    <p>Columbus State University</p>
                </div>
                <div class="content">
                    <p>Dear {student_name},</p>
                    <p>A new grade has been posted to your academic record:</p>
                    <div class="grade-box">
                        <p style="margin: 0; color: #6b7280;">{course_name}</p>
                        <p class="grade">{grade}</p>
                    </div>
                    <p>Log in to CougarWorks to view your updated GPA and academic standing.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from CougarWorks.</p>
                    <p>Columbus State University © {datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(student_email, subject, body_html)

    def send_progress_notification(self, student_email, student_name, progress_data):
        """Send a degree progress update notification."""
        subject = "Degree Progress Update"

        percentage = progress_data.get('percentage', 0)
        completed = progress_data.get('completedCredits', 0)
        required = progress_data.get('requiredCredits', 120)

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f7fb; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #003359 0%, #002240 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .progress-box {{ background: #f9fafb; border-radius: 12px; padding: 25px; margin: 20px 0; text-align: center; }}
                .progress-percentage {{ font-size: 48px; font-weight: bold; color: #003359; }}
                .progress-bar-container {{ background: #e5e7eb; border-radius: 10px; height: 20px; margin: 15px 0; }}
                .progress-bar-fill {{ background: linear-gradient(90deg, #003359, #C60C30); height: 100%; border-radius: 10px; width: {percentage}%; }}
                .footer {{ background: #f4f7fb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 CougarWorks</h1>
                    <p>Columbus State University</p>
                </div>
                <div class="content">
                    <p>Dear {student_name},</p>
                    <p>Here's your current degree progress:</p>
                    <div class="progress-box">
                        <p class="progress-percentage">{percentage}%</p>
                        <p style="color: #6b7280;">{completed} of {required} credits completed</p>
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill"></div>
                        </div>
                    </div>
                    <p>Keep up the great work! Log in to CougarWorks for detailed course tracking.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from CougarWorks.</p>
                    <p>Columbus State University © {datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(student_email, subject, body_html)

    def send_advisor_message(self, student_email, student_name, advisor_name, message):
        """Send a message from an advisor to a student."""
        subject = f"Message from Your Advisor: {advisor_name}"

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f7fb; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #C60C30 0%, #9a0a24 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .message-box {{ background: #f9fafb; border-left: 4px solid #003359; padding: 20px; margin: 20px 0; border-radius: 8px; font-style: italic; }}
                .footer {{ background: #f4f7fb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📧 Advisor Message</h1>
                    <p>Columbus State University</p>
                </div>
                <div class="content">
                    <p>Dear {student_name},</p>
                    <p>Your advisor, <strong>{advisor_name}</strong>, has sent you a message:</p>
                    <div class="message-box">
                        "{message}"
                    </div>
                    <p>Please log in to CougarWorks to respond or schedule an appointment.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from CougarWorks.</p>
                    <p>Columbus State University © {datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(student_email, subject, body_html)

    def send_registration_reminder(self, student_email, student_name, deadline, remaining_courses):
        """Send a registration reminder."""
        subject = f"Registration Reminder: {deadline}"

        courses_list = "".join([f"<li>{c.get('courseCode', '')} - {c.get('courseName', '')}</li>" for c in remaining_courses[:5]])

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f7fb; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #C60C30 0%, #9a0a24 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .deadline-box {{ background: #fef2f2; border: 2px solid #C60C30; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center; }}
                .deadline {{ font-size: 24px; font-weight: bold; color: #C60C30; }}
                .footer {{ background: #f4f7fb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ Registration Reminder</h1>
                    <p>Columbus State University</p>
                </div>
                <div class="content">
                    <p>Dear {student_name},</p>
                    <p>Don't forget to register for upcoming courses!</p>
                    <div class="deadline-box">
                        <p style="margin: 0;">Registration Deadline</p>
                        <p class="deadline">{deadline}</p>
                    </div>
                    <p>Recommended remaining courses:</p>
                    <ul>{courses_list}</ul>
                </div>
                <div class="footer">
                    <p>This is an automated message from CougarWorks.</p>
                    <p>Columbus State University © {datetime.now().year}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(student_email, subject, body_html)



notification_service = NotificationService()
