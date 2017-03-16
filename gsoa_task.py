import tasktiger
from redis import Redis 
from rpy2.robjects.packages import importr
import rpy2.robjects as ro
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
import smtplib

gsoa = importr('GSOA')

conn = Redis(host="redis")
tiger = tasktiger.TaskTiger(connection=conn)


NECESSARY_FIELDS = ['dataFilePath', 'classFilePath', 'gmtFilePath']
ACCEPTED_FIELDS = ['outFilePath', 'classificationAlgorithm', 'numCrossValidationFolds', 'numRandomIterations',
                   'numCores', 'removePercentLowestExpr', 'removePercentLowestVar'] + NECESSARY_FIELDS

@tiger.task()
def call_gsoa(request):
    print("request: {}".format(request))
    gsoa = importr('GSOA')
    conn = Redis(host="redis")
    tiger = tasktiger.TaskTiger(connection=conn)
    args = request.copy()
    for field in NECESSARY_FIELDS:
        args.pop(field)
    if len(str(request.get('dataFilePath'))) < 2:
        return "no data"
    outFilePath = "/data/{}".format(request.get('email', 'results_txt'))
    print("email: {}".format(request.get('email', 'results_txt')))       
    result =  gsoa.GSOA_ProcessFiles(dataFilePath=request.get('dataFilePath', ''),
                                     classFilePath=request.get('classFilePath', ''),
                                     gmtFilePath=request.get('gmtFilePath', ''),
                                     outFilePath=outFilePath,
                                     numRandomIterations=10)

    email_report(request.get('email'), outFilePath)


# send the email
def email_report(email_address, file_path):
    from_ = 'smacneil88@gmail.com'
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = 'GSOA Results'
    msgRoot['From'] = from_
    msgRoot['To'] = email_address


    
    msg = MIMEMultipart('alternative')
    text = MIMEText('Results File', 'plain')
    msgRoot.attach(msg)


    with open(file_path) as fp:
        attachment = MIMEBase('text', None)
        attachment.set_payload(fp.read())
        attachment.add_header('Content-Disposition', 'attachment', filename=file_path.split('/')[-1])
    msgRoot.attach(attachment)
    
    #msg.attach(text)
    mailer = smtplib.SMTP('smtp.gmail.com:587')
    mailer.starttls()
    mailer.login('smacneil88', 'Berkeley13')
    mailer.sendmail(from_, email_address, msgRoot.as_string())
    mailer.close()



