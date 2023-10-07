import re
import pandas as pd
from googletrans import Translator
from urlextract import URLExtract

# Text to be translated
def trans(Text):
    translator=Translator()
    return translator.translate(Text,src='en',dest='hi').text

def preprocess(data):
    pattern='\[\d{2}/\d{2}/\d{2},\s\d{2}:\d{2}:\d{2}\]\s'

    messages=re.split(pattern,data)[1:]
    dates=re.findall(pattern,data)

    date_pattern = r'\[(\d{2}/\d{2}/\d{2})'
    time_pattern = r', (\d{2}:\d{2}:\d{2})\]'

    date_list=[]
    time_list=[]
    for date in dates:
        date_match = re.search(date_pattern,date)
        time_match = re.search(time_pattern,date)
        date_list.append(date_match.group(1))
        time_list.append(time_match.group(1))

    df=pd.DataFrame({'message':messages,'dates':date_list,'time':time_list})
    df['date_time']=df['dates'] + " " + df['time']
    df['date_time']=pd.to_datetime(df['date_time'])

    user=[]
    message=[]
    for msg in df['message']:
        entry=re.split('([\w\W]+?):\s',msg)
        user.append(entry[1])
        if entry[2]:
            message.append(entry[2])
        elif entry[3]:
            message.append(entry[3])
    df['user']=user
    df['message']=message
    
    df.drop(['dates','time'],axis=1,inplace=True)

    df['date']=df['date_time'].dt.date
    df['day']=df['date_time'].dt.day_name()
    df['month_num']=df['date_time'].dt.month
    df['month']=df['date_time'].dt.month_name()
    df['year']=df['date_time'].dt.year
    df['hour']=df['date_time'].dt.hour
    df['minute']=df['date_time'].dt.minute

    df.drop('date_time',axis=1,inplace=True)

    period = []
    for hour in df[['day', 'hour']]['hour']:
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour + 1))
        else:
            period.append(str(hour) + "-" + str(hour + 1))

    df['period'] = period

    url=URLExtract()
    urls=[]
    for i in df['message']:
        link=url.find_urls(i)
        if link:
            urls.extend(link)
    def remove_links(text):
        x=[]
        for word in text.split():
            if word not in urls:
                x.append(word)
            else:
                x.append('0')
        return " ".join(x)
    df['message']=df['message'].apply(lambda x:x.replace('\n',' '))
    df['message']=df['message'].apply(remove_links)

    df['hindi']=df['message'].apply(lambda x:trans(x))

    with open('venv\positive_words_hi.txt','r',encoding="utf-8") as file:
        positive_words=[]
        lines=file.read().split('\n')
        for word in lines:
            positive_words.append(word)

    def positive(text):
        score=0
        for word in text.split():
            if word in positive_words:
                score+=1
        return score
    
    df['positive']=df['hindi'].apply(lambda x:positive(x))

    with open('venv\words_negative_hi.txt','r',encoding="utf-8") as file:
        negative_words=[]
        lines=file.read().split('\n')
        for word in lines:
            negative_words.append(word)

    def negative(text):
        score=0
        for word in text.split():
            if word in negative_words:
                score+=1
        return score
        
    df['negative']=df['hindi'].apply(lambda x:negative(x))

    return df