import json
import requests
import re
from datetime import datetime
from glob import glob
import xml.etree.ElementTree as xml


def sanitize_file_name(title):
    sanitized_title = re.sub(r'\s+', r'_', title)
    sanitized_title = re.sub(r'[^a-zA-Z0-9_-]', r'', sanitized_title)
    return sanitized_title[:100]
 
def extract_text(element):
    if element is not None:
        return element.text
    return None

def convert_pubDate_to_datetime(pubDate):
    date_val = None
    try:
        date_val = datetime.strptime(pubDate, '%a, %d %b %Y %H:%M:%S %z')
    except:
        date_val = datetime.strptime(pubDate, '%a, %d %b %Y %H:%M:%S %Z')
    return date_val


class Podcast:
    def __init__(self, pod_obj):
        self.show_title = pod_obj['show_title']
        self.folder_name = sanitize_file_name(self.show_title)
        self.rss_feed = pod_obj['rss_feed']
        self.last_ep_date = None
        last_ep_date_string = pod_obj['last_ep_date']
        self.file_path = ""
        if len(last_ep_date_string) > 0:
            self.last_ep_date = convert_pubDate_to_datetime(pod_obj['last_ep_date'])


    def get_json(self):
        pod_dict = dict(show_title = self.show_title, rss_feed = self.rss_feed)
        pod_dict['last_ep_date'] = "" if self.last_ep_date == None else self.last_ep_date
        return pod_dict


    def download_new_episodes(self):
        session = requests.Session()
        with session.get(self.rss_feed) as feed_response:
            if  not feed_response.ok:
                print("Failed to load RSS feed for {0}".format(self.show_title))
                return
            feed_content = feed_response.content
        feed_xml = xml.fromstring(feed_content)
        episode_list = feed_xml.findall('.//item')

        for i in range(1,len(episode_list)+1):
            episode = episode_list[-i] # iterate in reverse order
            pub_date_str = extract_text(episode.find('pubDate'))
            pub_date_datetime = convert_pubDate_to_datetime(pub_date_str)

            if self.last_ep_date != None and pub_date_datetime > self.last_ep_date:
                continue
            episode_title = extract_text(episode.find('title'))
            link = extract_text(episode.find('link'))
            if link == None:
                link = episode.find('.//enclosure').attrib['url']

            file_name = "{0}.mp3".format(sanitize_file_name(episode_title))

            with session.get(link, stream=True) as download_response:
                print("Attempting to download episode: {0}".format(episode_title))
                if not download_response.ok:
                    print("Failed to get episode from source: {0}".format(download_response.status_code))
                    return
                try:
                    with open(file_name, mode="wb") as file:
                        for chunk in download_response.iter_content(chunk_size=10 * 1024):
                            file.write(chunk)
                        print("Download complete")
                        self.last_ep_date = pub_date_str

                except:
                    print("Failed to open file for download: {0}".format(file_name))
                    return

            break #prevent downloading entire catalogue while testing

def main():

    try:
        with open('../conf/podcast.json') as f:
            d = json.load(f)
    except:
        print("FAILED to load config file")

    podcast_list = [Podcast(y) for y in d['podcasts']]

    for pod in podcast_list:
        pod.download_new_episodes()
 
    return 0

if __name__ == '__main__':
    main()