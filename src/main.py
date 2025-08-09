import json
from Podcast import Podcast 

def main():

    try:
        with open('../conf/podcast.json') as f:
            d = json.load(f)
    except:
        print("FAILED to load config file")

    podcast_list = [Podcast(y) for y in d['podcasts']]

    for pod in podcast_list:
        pod.download_new_episodes()
 
    # podcast_list[6].download_new_episodes()
    return 0

if __name__ == '__main__':
    main()