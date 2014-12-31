# -*- coding: utf-8
import csv
import sys
import json
import smtplib
from email.mime.text import MIMEText

def read_recipient_file(fname, recipient_id):
    with open(fname, "rb") as file:
        for row in csv.reader(file, delimiter="\t"):
            email_addr,id = row
            if id == recipient_id:
                return email_addr
    return None

def make_msg(sender_addr, recipient_addr, title, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = title
    msg["From"] = sender_addr
    msg["To"] = recipient_addr
    return msg

def send(conf, email_addr, msg_lines):
    smtps_host = conf["smtps_host"]

    conn = smtplib.SMTP_SSL(smtps_host)
    conn.ehlo_or_helo_if_needed()
        
    smtp_user = conf["smtp_user"]
    smtp_password = conf["smtp_password"]
    conn.login(smtp_user, smtp_password)

    conn.sendmail(conf["sender_address"], email_addr, msg_lines)

    conn.quit()

def read_config(conf_file_name):
    return json.load(open(conf_file_name, "rb"))
    
def main():
    args = sys.argv[1:]
    if len(args) >= 2:
        conf = read_config(args[0])
        email_file = conf["email_file"]
        
        recipient_id = args[1]
        title = conf["title"] % {"id":recipient_id}
        body = sys.stdin.read()
        
        recipient_addr = read_recipient_file(email_file, recipient_id)
        
        if recipient_addr is not None:
            msg = make_msg(conf["sender_address"], recipient_addr, title, body)
            send(conf, recipient_addr, msg.as_string())

    else:
        print "Usage: echo 'Email body' | send.py conf-file recipient-id"
    

if __name__ == '__main__':
    main()
