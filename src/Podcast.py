import requests
from glob import glob
import xml.etree.ElementTree as xml


month_map = {"Jan" : "01", "Feb" : "02", 
             "Mar" : "03", "Apr" : "04", 
             "May" : "05", "Jun" : "06",
             "Jul" : "07", "Aug" : "08",
             "Sep" : "09", "Oct" : "10",
             "Nov" : "11", "Dec" : "12",}
 
def extract_text(element):
    if element is not None:
        return element.text
    return None

def get_condensed_date(string_date):
    list_data = string_date.split()
    if len(list_data) < 4:
        return ''
    
    return list_data[3] + month_map[list_data[2]] + list_data[1]

class Podcast:
    def __init__(self, pod_obj):
        self.show_title = pod_obj['show_title']
        self.folder_name = pod_obj['folder_name']
        self.rss_feed = pod_obj['rss_feed']
        self.episodes = []

        self.refresh_episode_list()


    def refresh_episode_list(self):
        return 0
    
    def get_rss_feed_url(self):
        return self.rss_feed
    
    def get_episode_list(self):
        return self.episodes

    def download_new_episodes(self):
        feed_response = requests.get(self.rss_feed)
        feed_content = feed_response.content
        feed_xml = xml.fromstring(feed_content)
        episode_list = feed_xml.findall('.//item')

        for episode in episode_list:
            title = extract_text(episode.find('title'))
            link = extract_text(episode.find('link'))
            if link == None: #fix
                link = extract_text(episode.find('url'))
            description = extract_text(episode.find('itunes:summary'))
            if description == None: #fix
                description = extract_text(episode.find('description'))
            date = get_condensed_date(extract_text(episode.find('pubDate')))


            print("{0}{1}{2}{3}".format(title, link, description, date))
            
        

class Episode:
    def __init__(self, title, description, link, date_str):
        self.episode_title = title
        self.description = description
        self.link = link
