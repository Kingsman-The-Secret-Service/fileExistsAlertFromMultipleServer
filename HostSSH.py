import os.path
import paramiko
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import MailConfiguration
import socket
import re

class SSHClient():
    def calculateParallel(self, data, threads=2):
        pool = ThreadPool(threads)
        results = pool.map(self.connect_host, data)
        pool.close()
        pool.join()
        return results

    def mailAlert(self, data):
        config = MailConfiguration.read_config()
        smtp = config.get('main', 'smtp')
        smtp_port = config.get('main', 'smtp_port')
        mail = config.get('main', 'e-mail')
        password = config.get('main', 'password')
        subject = config.get('main', 'subject')

        receiver = data['email']
        if not receiver:
            receiver = config.get('main', 'receiver')
        try:
            server = smtplib.SMTP(smtp, int(smtp_port))
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(mail, password)
            msg = MIMEMultipart()
            msg['From'] = mail
            msg['To'] = receiver
            msg['Subject'] = subject
            body = "File Created"
            msg.attach(MIMEText(body, 'plain'))
            text = msg.as_string()
            server.sendmail(mail, receiver, text)
        except smtplib.SMTPAuthenticationError as e:
            print e
            return

    def checkHost(self, server, user, pwd):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(server, username=user, password=pwd)
            return 'working'
        except paramiko.BadHostKeyException, e:
            print e
            return 'Error'
        except paramiko.AuthenticationException, e:
            print e
            return 'Error'
        except paramiko.SSHException, e:
            print e
            print 'Error'
        except socket.error as e:
            print 'socket =', e
            return 'Error'

    def connect_host(self, data):
        try:
            server, username, password = (data['ip_address'], data['username'], data['password'])
            # port = data['port']
            ssh = paramiko.SSHClient()
            paramiko.util.log_to_file("ssh.log")
            print 'connecting host...'
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            conn = ssh.connect(server, username=username, password=password)
            if conn is None:
                print 'Connection successful.'
            else:
                print 'connection failed'
            sftp = ssh.open_sftp()
            try:
                folderPath = str(data['dir_path'])
                list = sftp.listdir(folderPath)
                if not list == []:
                    fileExt = str(data['file_name'])
                    if not fileExt:
                        self.mailAlert(data)
                    else:
                        patern = re.compile(r"[^\\]%s$" % fileExt, re.I)
                        filtered_files = [f for f in list if patern.search(f)]
                        if filtered_files == []:
                            if any(fileExt in s for s in list):
                                # print 'yes'
                                self.mailAlert(data)
                            else:
                                print 'No'
                        else:
                            self.mailAlert(data)
                            print filtered_files
                else:
                    print 'No files in this directory.'
                    # for element in list:
                    #     print '=', element
            except IOError as e:
                print e
                return
            finally:
                sftp.close()
                ssh.close()
        except paramiko.AuthenticationException:
            output = "Authentication Failed"
            print output
