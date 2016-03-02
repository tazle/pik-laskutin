# -*- coding: utf-8
import csv
import sys
import json
import smtplib
import os
import time
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

        dir_name = args[1]
        for fname in os.listdir(dir_name):
            if fname.endswith(".txt"):
                path = os.path.join(dir_name, fname)
                recipient_id = fname.replace(".txt","")

                title = conf["title"] % {"id":recipient_id}
                body = open(path, "rb").read()
        
                recipient_addr = read_recipient_file(email_file, recipient_id)
        
                print >> sys.stderr, "Sending", recipient_id, recipient_addr
                if recipient_addr:
                    msg = make_msg(conf["sender_address"], recipient_addr, title, body)
                    while True:
                        try:
                            send(conf, recipient_addr, msg.as_string())
                            print >> sys.stderr, "Sent", recipient_id, recipient_addr
                            break # No need to retry
                        except smtplib.SMTPRecipientsRefused, e:
                            error_code = e.recipients.values()[0][0]
                            if error_code == 501:
                                print >> sys.stderr, "Invalid recipient, not retrying", recipient_id, recipient_addr, e
                                break # Break retry loop
                            elif error_code == 451:
                                print >> sys.stderr, "Throttled, retrying later", recipient_id, recipient_addr, e
                            else:
                                print >> sys.stderr, "Unknown error, not retrying", recipient_id, recipient_addr, e
                                break # Break retry loop
                        except Exception, e:
                            print >> sys.stderr, "Unknown exception type, not retrying", recipient_id, recipient_addr, e
                            break # Break retry loop
                        time.sleep(60)
                else:
                    print >> sys.stderr, "No e-mail address for", recipient_id
    else:
        print "Usage: send.py conf-file recipient-id"
    

if __name__ == '__main__':
    main()
