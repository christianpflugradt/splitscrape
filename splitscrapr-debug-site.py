from sys import argv
import traceback
import urllib.request
import yaml

def main():
    try:
        with open(argv[1] if len(argv) == 3 else 'splitscrapr.yml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        sitename = argv[2] if len(argv) == 3 else argv[1]
        site = next(filter(lambda site : site['name'] == sitename, config['sites']))
        content = urllib.request.urlopen(urllib.request.Request(site['url'], headers={'User-Agent': config['http']['useragent']})).read().decode('utf-8').replace('\r', '')
        suffix = 0
        with open('%s-%d' % (sitename, suffix), 'wb') as f:
            f.write(content.encode('utf-8'))
        for split in site['splits']:
            suffix += 1
            content = content.split(split['match'])[split['pos']]
            with open('%s-%d' % (sitename, suffix), 'wb') as f:
                f.write(content.encode('utf-8'))
    except:
        traceback.print_exc()
        print("""
Execution failed.

Make sure you\'ve passed a valid config and an existing site name.

Script parameter options:
1.) path-to-config site-name
2.) site-name

Example: Python3 splitscrapr-debug-site.py splitscrapr.yml examplesite
        """)

if __name__ == '__main__':
    main()

