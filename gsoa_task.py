import tasktiger
from redis import Redis 
from rpy2.robjects.packages import importr
from rpy2 import rinterface
import rpy2.robjects as ro
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
import smtplib
from rpy2.robjects import ListVector
import sys # DELETE

gsoa = importr('GSOA')
rmarkdown = importr('rmarkdown')

conn = Redis(host="redis")
tiger = tasktiger.TaskTiger(connection=conn)


NECESSARY_FIELDS = ['dataFilePath', 'classFilePath', 'gmtFilePath']
ACCEPTED_FIELDS = ['outFilePath', 'classificationAlgorithm', 'numCrossValidationFolds', 'numRandomIterations',
                   'numCores', 'removePercentLowestExpr', 'removePercentLowestVar'] + NECESSARY_FIELDS

@tiger.task()
def call_gsoa(request):
    print("request: {}".format(request))
    print(NECESSARY_FIELDS)
    local_buffer = []
    try:
        gsoa = importr('GSOA')
        args = request.copy()
        for field in NECESSARY_FIELDS:
            args.pop(field)
        if len(str(request.get('dataFilePath'))) < 2:
            return "no data"
        outFilePath = "/data/{}.txt".format(request.get('email', 'results_txt').replace('.com', ''))
        print("email: {}".format(request.get('email', 'results_txt')))
        rinterface.set_writeconsole_warnerror(lambda line: local_buffer.append(line))
        rinterface.set_writeconsole_regular(lambda line: local_buffer.append(line))
        result =  gsoa.GSOA_ProcessFiles(dataFilePath=request.get('dataFilePath', ''),
                                         classFilePath=request.get('classFilePath', ''),
                                         gmtFilePath=request.get('gmtFilePath', ''),
                                         outFilePath=outFilePath,
                                         numRandomIterations=request.get('numRandomIterations', ''),
                                         classificationAlgorithm=request.get('classificationAlgorithm', ''), 
                                         numCrossValidationFolds=request.get('numCrossValidationFolds', ''), 
                                         removePercentLowestExpr=request.get('removePercentLowestExpr', ''), 
                                         removePercentLowestVar=request.get('removePercentLowestVar', ''))
        print("Writing RMarkdown")
        outFilePath_html=outFilePath.replace('txt', 'html')
        rmarkdown.render('/app/GSOA_Report.Rmd', output_file = outFilePath.replace('txt', 'html'),
            params=ListVector({'data1': outFilePath}))
        email_report(request.get('email'), outFilePath)
    except Exception as e:
        email_error(request.get('email'), e, local_buffer)
    finally:
        rinterface.set_writeconsole_warnerror(rinterface.consolePrint)
        rinterface.set_writeconsole_regular(rinterface.consolePrint)


#@tiger.task()
#def call_gsoa_hallmarks(request):
#    print("request: {}".format(request))
#    print(NECESSARY_FIELDS)
#    try:
#        gsoa = importr('GSOA')
#        conn = Redis(host="redis")
#        tiger = tasktiger.TaskTiger(connection=conn)
#        args = request.copy()
#        for field in NECESSARY_FIELDS:
#            args.pop(field)
#        if len(str(request.get('dataFilePath'))) < 2:
#            return "no data"
#        outFilePath = "/data/{}.txt".format(request.get('email', 'results_txt').replace('.com', ''))
#        print("email: {}".format(request.get('email', 'results_txt')))       
#        result =  gsoa.GSOA_ProcessFiles(dataFilePath=request.get('dataFilePath', ''),
#                                         classFilePath=request.get('classFilePath', ''),
#                                         gmtFilePath=request.get('gmtFilePath', ''),
#                                         outFilePath=outFilePath,
#                                         numRandomIterations=request.get('numRandomIterations', ''),
#                                         classificationAlgorithm=request.get('classificationAlgorithm', ''), 
#                                         numCrossValidationFolds=request.get('numCrossValidationFolds', ''), 
#                                         removePercentLowestExpr=request.get('removePercentLowestExpr', ''), 
 #                                        removePercentLowestVar=request.get('removePercentLowestVar', ''))
 #       print("Writing RMarkdown")
 #       outFilePath_html=outFilePath.replace('txt', 'html')
 #       rmarkdown.render('/app/GSOA_Report.Rmd', output_file = outFilePath.replace('txt', 'html'),
 #           params=ListVector({'data1': outFilePath}))
 #       email_report(request.get('email'), outFilePath)
 #   except Exception as e:
 #       email_error(request.get('email'), e)





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
    
    with open(file_path.replace('txt', 'html')) as fp:
        attachment1 = MIMEBase('html', None)
        attachment1.set_payload(fp.read())
        attachment1.add_header('Content-Disposition', 'attachment', filename=file_path.split('/')[-1].replace('txt', 'html'))
    msgRoot.attach(attachment1)
    #msg.attach(text)
    mailer = smtplib.SMTP('smtp.gmail.com:587')
    mailer.starttls()
    mailer.login('smacneil88', 'Berkeley13')
    mailer.sendmail(from_, email_address, msgRoot.as_string())
    mailer.close()


def email_error(email_address, exception, local_buffer):
    from_ = 'smacneil88@gmail.com'
    msg = MIMEMultipart()
    msg['From'] = from_
    msg['To'] = email_address
    msg['Subject'] = "GSOA ERROR"
    msg.preamble = 'GSOA Returned the Following Error'
    body = "Error message: {}: \n {}".format(exception, '\n'.join(local_buffer))
    msg.attach(MIMEText(body, 'plain'))
    #msg.attach(text)
    mailer = smtplib.SMTP('smtp.gmail.com:587')
    mailer.starttls()
    mailer.login('smacneil88', 'Berkeley13')
    mailer.sendmail(from_, email_address, msg.as_string())
    mailer.close()

