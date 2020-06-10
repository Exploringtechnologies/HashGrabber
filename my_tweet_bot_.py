#importing all recommended libraries
import tweepy
import json
import time
import os
import csv
import schedule
import datetime

#loading credentials
def load_api():
    try:
        with open('keys.json','r') as k:
            keys = json.load(k)
        authorization = tweepy.OAuthHandler(keys["CONSUMER_KEY"],keys["CONSUMER_SECRET"])
        authorization.set_access_token(keys["ACCESS_KEY"], keys["ACCESS_SECRET"])
        api = tweepy.API(authorization)
        return api
    except:
        print("Error on keys.json")
        return None

#gather only english tweets
def isEnglish(text):
    try:
        text.encode(encoding='utf=8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True
    
#grabing location associated with hashtag trends (WHERE ON EARTH IDENTIFIERS)
def get_WOEID(api, locations):
    tweet_location = api.trends_available()
    places = {loc['name'].lower() : loc['woeid'] for loc in tweet_location};
    woeids = []
    for location in locations:
        if location in places:
            woeids.append(places[location])
        else:
            print("Err: ",location," does not exist in trending topics")
        return woeids
    
'''
Getting Tweets for the given hashtag with max of 500 popular tweets with english lang
'''
def get_tweets(api, query):
    tweets = []
    for status in tweepy.Cursor(api.search,
                       q=query,
                       count=500,
                       result_type='popular',
                       include_entities=True,
                       monitor_rate_limit=True, 
                       wait_on_rate_limit=True,
                       lang="en").items():
     
        # Getting tweets which only has english lang
        if isEnglish(status.text) == True:
            tweets.append([status.id_str, query, status.created_at.strftime('%d-%m-%Y %H:%M'), status.user.screen_name, status.text])
    return tweets

#fetching trending hashtags for given location

def get_trending_hashtags(api, location):
    woeids = get_WOEID(api, location)
    trending = set()
    for woeid in woeids:
        try:
            trends = api.trends_place(woeid)
        except:
            print("API limit exceeded. Waiting for next hour")
            time.sleep(5) # change to 5 for testing
            trends = api.trends_place(woeid)
        # Checking for English dialect Hashtags and storing text without #
        topics = [trend['name'][1:] for trend in trends[0]['trends'] if (trend['name'].find('#') == 0 and isEnglish(trend['name']) == True)]
        trending.update(topics)
    
    return trending    
    
#everything in one place
def twitter_bot(api, locations):
    today = datetime.datetime.today().strftime("%d-%m-%Y")
    if not os.path.exists("trending_tweets"):
        os.makedirs("trending_tweets")
    file_tweets = open("trending_tweets/"+today+"-tweets.csv", "a+")
    file_hashtags = open("trending_tweets/"+today+"-hashtags.csv", "w+")
    writer = csv.writer(file_tweets)
    
    hashtags = get_trending_hashtags(api, locations)
    file_hashtags.write("\n".join(hashtags))
    print("Hashtags written to file.")
    file_hashtags.close()
    
    for hashtag in hashtags:
        try:
            print("Getting Tweets for the hashtag: ", hashtag)
            tweets = get_tweets(api, "#"+hashtag)
        except:
            print("API limit exceeded. Waiting for next hour")
            time.sleep(0.2) # change to 0.2 sec for testing
            tweets = get_tweets(api, "#"+hashtag)
        for tweet in tweets:
            writer.writerow(tweet)
    
    file_tweets.close()
    
#main function to initialize all task & methods
    
def main():
    ''' 
    Use location = [] list for getting trending tags from different countries. 
    I have limited number of request hence I am using only 1 location
    '''
    #locations = ['new york', 'los angeles', 'philadelphia', 'barcelona', 'canada', 'united kingdom', 'india']        
    
    locations = [input("which country trends you want to grab: ").lower()]
    api = load_api()
    
    #schedule.every().day.at("00:00").do(twitter_bot, api, locations)
    schedule.every(10).seconds.do(twitter_bot, api, locations)
    while True:
        schedule.run_pending()
        time.sleep(1)
        
if __name__ == "__main__":
    main()