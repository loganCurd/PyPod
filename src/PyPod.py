import json
import requests
import re
import os
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
    def __init__(self, pod_obj, download_folder):
        self.show_title = pod_obj['show_title']
        self.rss_feed = pod_obj['rss_feed']
        self.last_ep_date = None
        last_ep_date_string = pod_obj['last_ep_date']
        self.file_path = "{0}/{1}".format(download_folder, sanitize_file_name(self.show_title))
        os.makedirs(self.file_path, exist_ok=True)
        if len(last_ep_date_string) > 0:
            self.last_ep_date = convert_pubDate_to_datetime(pod_obj['last_ep_date'])


    def get_pod_obj(self):
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

            if self.last_ep_date != None and pub_date_datetime <= self.last_ep_date: # already downloaded
                continue
            
            episode_title = extract_text(episode.find('title'))
            link = extract_text(episode.find('link'))
            if link == None:
                link = episode.find('.//enclosure').attrib['url']

            file_name = "{0}/{1}.mp3".format(self.file_path, sanitize_file_name(episode_title))

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

def main():

    try:
        with open('../conf/podcast.json', 'r') as in_file:
            conf_data = json.load(in_file)
    except:
        print("FAILED to load config file")
        return

    download_folder = conf_data['download_directory']

    podcast_list = [Podcast(y, download_folder) for y in conf_data['podcasts']]

    pod_conf_list = []

    for pod in podcast_list:
        pod.download_new_episodes()
        pod_conf_list.append(pod.get_pod_obj())

    conf_dict = dict(download_directory = download_folder, podcasts = pod_conf_list)

    try:
        with open('../conf/podcast.json', 'w') as out_file:
            json.dump(conf_dict, out_file)
    except:
        print("FAILED to write new data to config file")
 
    return 0

if __name__ == '__main__':
    main()