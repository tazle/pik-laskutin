# -*- coding: utf-8
import csv
import sys
import json
import smtplib
import os
import time
from email.mime.text import MIMEText
import getpass

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
    #smtp_password = conf["smtp_password"]
    smtp_password = getpass.getpass()
    conn.login(smtp_user, smtp_password)

    conn.sendmail(conf["sender_address"], email_addr, msg_lines)

    conn.quit()

  
    
def get_connection(conf):
    # Function for establishing and returning an smtp connection
    # to given host
    smtps_host = conf["smtps_host"]

    conn = smtplib.SMTP_SSL(smtps_host)
    conn.ehlo_or_helo_if_needed()
        
    smtp_user = conf["smtp_user"]
    smtp_password = conf["smtp_password"]
    # smtp_password = getpass.getpass()

    conn.login(smtp_user, smtp_password)
    
    return conn
    
    
def read_config(conf_file_name):
    return json.load(open(conf_file_name, "rb"))
    
def main():
    args = sys.argv[1:]
    if len(args) >= 2:
        conf = read_config(args[0])
        email_file = conf["email_file"]

        # Get SMTP connection:
        conn = get_connection(conf)
        
        dir_name = args[1]
        for fname in os.listdir(dir_name):
            if fname.endswith(".txt"):
                path = os.path.join(dir_name, fname)
                recipient_id = fname.replace(".txt","")

                title = conf["title"] % {"id":recipient_id}
                body = open(path, "rb").read()
        
                recipient_addr = read_recipient_file(email_file, recipient_id)
        
                print("Sending", recipient_id, recipient_addr, file=sys.stderr)
                if recipient_addr:
                    msg = make_msg(conf["sender_address"], recipient_addr, title, body)
                    while True:
                        try:
                            #send(conf, recipient_addr, msg.as_string()) # Replaced with send_v2:
                            #send_v2(conn, conf, recipient_addr, msg.as_string())
                            # TBD: check if conn is connected
                            conn.sendmail(conf["sender_address"], recipient_addr, msg.as_string())
                            print("Sent", recipient_id, recipient_addr, file=sys.stderr)
                            break # No need to retry
                        except smtplib.SMTPRecipientsRefused as e:
                            error_code = list(e.recipients.values())[0][0]
                            if error_code == 501:
                                print("Invalid recipient, not retrying", recipient_id, recipient_addr, e, file=sys.stderr)
                                break # Break retry loop
                            elif error_code == 451:
                                print("Throttled, retrying later", recipient_id, recipient_addr, e, file=sys.stderr)
                            else:
                                print("Unknown error, not retrying", recipient_id, recipient_addr, e, file=sys.stderr)
                                break # Break retry loop
                        except Exception as e:
                            print("Unknown exception type, not retrying", recipient_id, recipient_addr, e, file=sys.stderr)
                            break # Break retry loop
                        time.sleep(60)
                else:
                    print("No e-mail address for", recipient_id, file=sys.stderr)
                   
        # End SMTP connection
        conn.quit()
        print("SMTP connection closed")
        
    else:
        print("Usage: send.py conf-file recipient-id")
    

if __name__ == '__main__':
    main()
