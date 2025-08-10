import requests
import re
from datetime import datetime
from glob import glob
import xml.etree.ElementTree as xml


def create_file_name(date, title):
    date = get_condensed_date_str(date)
    sanitized_title = re.sub(r'\s+', r'_', title)
    sanitized_title = re.sub(r'[^a-zA-Z0-9_]', r'', sanitized_title)
    sanitized_title = "{0}_{1}".format(date, sanitized_title)
    return "{0}.mp3".format(sanitized_title[:100])
 
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

def get_condensed_date_str(datetime):
    return datetime.strftime("%Y%m%d")

class Podcast:
    def __init__(self, pod_obj):
        self.show_title = pod_obj['show_title']
        self.folder_path = pod_obj['folder_path']
        self.rss_feed = pod_obj['rss_feed']
        self.last_ep_date = None
        last_ep_date_string = pod_obj['last_ep_date']
        if len(last_ep_date_string) > 0:
            self.last_ep_date = convert_pubDate_to_datetime(pod_obj['last_ep_date'])
        self.episodes = []

        self.refresh_episode_list()


    def refresh_episode_list(self):
        return 0

    def download_new_episodes(self):
        #convert to session
        with requests.get(self.rss_feed) as feed_response:
            if  not feed_response.ok:
                print("Failed to load RSS feed for {0}".format(self.show_title))
                return
            feed_content = feed_response.content
        feed_xml = xml.fromstring(feed_content)
        episode_list = feed_xml.findall('.//item')

        for i in range(1,len(episode_list)+1): #go in reverse order
            episode = episode_list[-i]
            pub_date_str = extract_text(episode.find('pubDate'))
            pub_date_datetime = convert_pubDate_to_datetime(pub_date_str)

            if self.last_ep_date != None and pub_date_datetime < self.last_ep_date:
                continue
            episode_title = extract_text(episode.find('title'))
            link = extract_text(episode.find('link'))
            if link == None: #fix
                link = extract_text(episode.find('url'))
            description = extract_text(episode.find('itunes:summary'))
            if description == None: #fix
                print("GOT WORSE DESCRIPTION")
                description = extract_text(episode.find('description'))

            file_name = create_file_name(pub_date_datetime, episode_title)

            with requests.get(link, stream=True) as download_response: #need to tag
                print("Attempting to download episode: {0}".format(episode_title))
                if not download_response.ok:
                    print("Failed to get episode from source: {0}".format(link))
                    continue
                try:
                    with open(file_name, mode="wb") as file:
                        for chunk in download_response.iter_content(chunk_size=10 * 1024):
                            file.write(chunk)
                        print("Download complete")

                except:
                    print("Failed to open file for download: {0}".format(file_name))

            break #prevent downloading entire catalogue while testing

            
        

class Episode:
    def __init__(self, title, description, link, date_str):
        self.episode_title = title
        self.description = description
        self.link = link
