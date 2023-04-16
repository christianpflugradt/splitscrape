from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging.handlers import RotatingFileHandler
from sys import argv
import logging
import os.path
import smtplib
import urllib.request
import yaml

log = None

# use more elegant match syntax once ubuntu moves to Python3.10
#def toLogLevel(level):
#    match level:
#        case 'debug': return logging.DEBUG
#        case 'warn': return logging.WARN
#        case 'error': return logging.ERROR
#        case _: return logging.INFO

def toLogLevel(level):
    if level == 'debug':
        return logging.DEBUG
    elif level == 'warn':
        return logging.WARN
    elif level == 'error':
        return logging.ERROR
    else:
        return logging.INFO

def setup_logging(config):
    global log
    f = logging.Formatter(fmt=config['format'], datefmt=config['dateformat'])
    log = logging.getLogger(__name__)
    if config['logtostdout']:
        h = logging.StreamHandler()
        h.setFormatter(f)
        log.addHandler(h)
    fileconfig = config['file']
    if fileconfig['logtofile']:
        h = RotatingFileHandler(fileconfig['filename'], maxBytes=fileconfig['maxbytes'], backupCount=fileconfig['backups'])
        h.setFormatter(f)
        log.addHandler(h)
    log.setLevel(toLogLevel(config['level']))

def readConfig(name):
    with open(name, 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def download_content(site, httpconfig):
    log.debug('processing "%s"' % site['name'])
    req = urllib.request.Request(site['url'], headers={'User-Agent': httpconfig['useragent']})
    log.debug('sending request to "%s"' % site['url'])
    content = urllib.request.urlopen(req).read().decode('utf-8').replace('\r', '')
    log.debug('content downloaded')
    return content

def match(content, splits):
    splitted = content
    for split in splits:
        splitted = splitted.split(split['match'])[split['pos']]
    return splitted

def ref_exists(site):
    return os.path.isfile(site['name'])

def load_ref(site):
    with open(site['name'], 'r') as f:
        return f.read()

def move_backup(file):
    if os.path.isfile(file):
        target = '%s-1' % file
        if '-' in file:
            base, suffix = file.rsplit('-', maxsplit=1)
            target = '%s-%d' % (base, int(suffix)+1)
        os.rename(file, target)

def update_definition(site, content):
    name = site['name']
    backups = site['backups']
    if backups > 0:
        if backups > 1:
            for i in range(backups-1, 0, -1):
                move_backup('%s-%d' % (name, i))
        move_backup(name)
    with open(name, 'wb') as f:
        f.write(content.encode('utf-8'))

def send_mail(smtp, site, content):
    smtpclient = smtplib.SMTP(smtp['server'], smtp['port'])
    smtpclient.starttls()
    smtpclient.login(smtp['user'], smtp['password'])
    msg = MIMEMultipart('alternative')
    msg['From'] = smtp['user']
    msg['To'] = ', '.join(site['recipients'])
    msg['Subject'] = '[splitscrapr] update: %s' % site['name']
    extra = site['extracontent']
    if extra['fixrelativelinks']:
        content = content.replace(' href="/', ' href="%s/' % ''.join(site['url'].split('/', 3)[:3]))
    msg.attach(MIMEText('%s%s%s' % (extra['pre'], content, extra['post']), site['contenttype']))
    smtpclient.send_message(msg)
    smtpclient.quit()

def process_site(site, config):
    if not site['enabled']:
        log.debug('skipping disabled site "%s"' % site['name'])
    else:
        try:
            content = download_content(site, config['http'])
        except:
            log.exception('scraping site "%s" failed' % site['name'])
            return
        try:
            content = match(content, site['splits'])
        except:
            log.exception('splitting content for site "%s" failed' % site['name'])
            return
        if ref_exists(site):
            if content != load_ref(site):
                log.info('definition for "%s" has changed; updation definition' % site['name'])
                try:
                    update_definition(site, content)
                except:
                    log.exception('definition update for site "%s" failed' % site['name'])
                    return
                log.debug('sending email to "%s" to inform about changed definition of "%s"' % (', '.join(site['recipients']), site['name']))
                try:
                    send_mail(config['smtp'], site, content)
                except:
                    log.exception('sending email for site "%s" failed' % site['name'])
                    return
            else:
                log.debug('definition for "%s" hasn\'t changed' % site['name'])
        else:
            log.info('no definition for "%s" found; writing initial definition' % site['name'])
            update_definition(site, content)

def main():
    try:
        config = readConfig(argv[1] if len(argv) == 2 else 'splitscrapr.yml')
        setup_logging(config['logging'])
    except Exception as e:
        print('FATAL ERROR: Configuration could not be loaded or logging not be initialized. Check your configuration! Exception: %s' % e)
    log.debug('### STARTING UP SPLITSCRAPr ###')
    log.debug('processing %d sites' % len(config['sites']))
    for site in config['sites']:
        try:
            process_site(site, config)
        except:
            log.exception('scraping site "%s" failed' % site['name'])
    log.debug('### SHUTTING DOWN SPLITSCRAPr ###')

if __name__ == '__main__':
    main()

