"""
TASK
Write a vacation auto responder application that does the following:
1. Checks for new emails in a given Gmail ID.
2. Replies to emails that have no prior replies.
3. Adds a label to the replied email and moves the email to the label.
4. Repeats task in random intervals of 45 to 120 secs.
5. Ensure no double replies are sent to any email at any point of time.
Note - You have to reply to the emails instead of sending new emails.

"""


import time
import random
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import base64

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes=['https://mail.google.com/'])
flow.run_local_server(port=8080, prompt='consent')
credentials = flow.credentials
print(f"Refresh token: {credentials.refresh_token}")
print(credentials.client_id)


# Set up Gmail API client
# credentials = Credentials.from_authorized_user_file('credentials.json')
service = build('gmail', 'v1', credentials=credentials)


def check_new_emails():
    # Get the list of unread emails
    response = service.users().messages().list(userId='me', q='is:unread').execute()
    messages = response.get('messages', [])

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        thread_id = msg['threadId']
        subject = get_header_value(msg['payload']['headers'], 'Subject')
        from_email = get_header_value(msg['payload']['headers'], 'From')
        original_message = msg['payload']['headers'][0]['value']

        # Check if the email has no prior replies
        if not has_prior_replies(thread_id):
            # Reply to the email
            reply_text = 'Thank you for your email. I am currently on vacation and will respond to you when I return.'
            send_reply(thread_id, from_email, subject, reply_text, original_message)


def get_header_value(headers, name):
    for header in headers:
        if header['name'] == name:
            return header['value']
    return ''


def has_prior_replies(thread_id):
    # Check if the email thread has any replies
    response = service.users().threads().get(userId='me', id=thread_id).execute()
    messages = response.get('messages', [])

    # If there is more than one message in the thread, it has prior replies
    return len(messages) > 1


def send_reply(thread_id, to_email, subject, reply_text, original_message):
    # Create the reply message
    reply_message = create_message(to_email, subject, reply_text, original_message)
    encoded_message = base64.urlsafe_b64encode(reply_message.encode("utf-8")).decode("utf-8")

    # Send the reply
    service.users().messages().send(
        userId='me',
        body={
            'raw': encoded_message,
            'threadId': thread_id
        }
    ).execute()

    # Add a label to the replied email and move it to the label
    label_id = get_label_id('INBOX')  # Replace 'Label Name' with the actual label name
    service.users().threads().modify(
        userId='me',
        id=thread_id,
        body={'addLabelIds': [label_id], 'removeLabelIds': ['UNREAD']}
    ).execute()


def get_label_id(inbox):
    labels = service.users().labels().list(userId='me').execute()
    for label in labels['labels']:
        if label['name'] == inbox:
            return label['id']
    return None


def create_message(to_email, subject, reply_text, original_message):
    message = f"From: me\r\nTo: {to_email}\r\nSubject: Re: {subject}\r\nIn-Reply-To: {original_message}\r\n\r\n{reply_text}"
    return message.encode('utf-8').decode('latin-1')


def main():
    while True:
        check_new_emails()
        time.sleep(random.randint(45, 120))


if __name__ == '__main__':
    main()
