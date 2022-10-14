from multiprocessing.connection import wait
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
# from django_thread import Thread as threading
import threading
import re
import spacy
import json
import time
sp = spacy.load('en_core_web_sm')

gChromeOptions = webdriver.ChromeOptions()
gChromeOptions.add_argument("window-size=1920x1480")
gChromeOptions.add_argument("disable-dev-shm-usage")
gChromeOptions.add_argument('--no-sandbox')
gChromeOptions.add_argument("--disable-gpu")
gChromeOptions.add_argument("--headless")

def check_position(biography):
    positions = ['president', 'vice president', 'chair', 'general chair', 'secretary', 'program chair', 'committee', 'director']
    count = 0
    for position in positions:
        if biography.find(position) != -1:
            count = count + 1
    # TODO: Check Weight of Position
    weight = 0.15
    if count > 0:
        return weight
    else:
        return 0

def citations_per_paper_score(citations, number_of_papers):
    citations_per_paper = citations / number_of_papers
    if citations_per_paper < 5 :
        return 0.03 * citations_per_paper
    else :
        return 0.15

def publications_per_year_score(publication, start_year, end_year):
    # print(publication, start_year, end_year)
    publications_per_year = publication / (end_year - start_year + 1)
    if publications_per_year < 3:
        return 0.15 * publications_per_year / 2
    elif publications_per_year < 6:
        return 0.15 * (6 - publications_per_year) / 2
    else:
        return 0

def experience_score(start_year, end_year):
    time_duration = end_year - start_year + 1
    if time_duration < 16:
        return 0.15 * time_duration / 15
    else:
        return 0.15

def check_topic_relevance(keywords, publication_topics):
    text_tokens = list(keywords)
    publication_topics = list(publication_topics)
    all_stopwords = sp.Defaults.stop_words
    tokens_without_stopwords = [word for word in text_tokens if not word in all_stopwords]
    relevant_topics = [word for word in tokens_without_stopwords for topic in publication_topics if topic == word]
    if len(relevant_topics) == len(tokens_without_stopwords):
        return 0.4
    else:
        return 0.4 * len(relevant_topics) / len(tokens_without_stopwords)

import warnings
import json
warnings.filterwarnings("ignore")

author_profiles = []

def profiling1(link1,keywords):
    driver1 = webdriver.Chrome(chrome_options=gChromeOptions, executable_path=ChromeDriverManager().install())
    keywords = re.split(',|\s+|_', keywords)
    keywords = set(keywords)
    authorScore = 0
    
    driver1.get(link1)
    driver1.implicitly_wait(30)
    
    try:
        l = driver1.find_element("link text", "Show More")
        driver1.execute_script('arguments[0].click()', l)
    except:
        pass
    

    name = (driver1.find_elements(By.XPATH,"//h1[contains(@class,'hide-mobile')]"))[0].text
    publication_topics_list = driver1.find_elements(By.XPATH,"//div[contains(@class,'research-areas')]")
    publication = (driver1.find_elements(By.XPATH,"//div[contains(@class,'publications col-6 text-base-md-lh')]"))
    publication_count = int((publication[0].text.replace(",","")).split("\n")[1])
    citation = (driver1.find_elements(By.XPATH,"//div[contains(@class,'citations col-6')]"))
    citation_count = int(int((int(citation[1].text.replace(",", "").split("\n")[1]))))
    start_year = int((driver1.find_elements(By.XPATH,"//span[contains(@class,'start-year col-6')]"))[1].text)
    end_year = int((driver1.find_elements(By.XPATH,"//span[contains(@class,'end-year col-6')]"))[1].text)
    
    publication_topics_list = (((publication_topics_list[0].text).replace("Publication Topics","")))
    # publication_topics_list = re.split(',|\s+', publication_topics_list)
    # publication_topics_list = set(publication_topics_list)

    biography = ""
    try:
        try:
            l = driver1.find_element("link text", "Show More")
            driver1.execute_script('arguments[0].click()', l)
        except:
            pass
        biography = ((driver1.find_elements(By.XPATH,"//div[contains(@class,'biography')]"))[0]).text 
    except:
        pass

    author_score =  check_position(biography) + check_topic_relevance(keywords, publication_topics_list) + publications_per_year_score(publication_count, start_year, end_year) + citations_per_paper_score(citation_count, publication_count) + experience_score(start_year, end_year)

    driver1.close()
    output = {
                'name': name, 
                'citation_count': citation_count, 
                'publication_count' : publication_count, 
                'publication_topics_list': publication_topics_list, 
                'biography': biography, 
                'author_score': author_score
            }
    author_profiles.append(output)
    return None

@api_view(['GET'])
def authorProfiling(request):
    list = ["image theory analysis and image","https://ieeexplore.ieee.org/author/37283451200","https://ieeexplore.ieee.org/author/37086061607", "https://ieeexplore.ieee.org/author/37085753500"]

    if request.method == 'GET':
        number_of_authors = len(list)-1
        keywords = list[0]
        authors=[]
        for itr in range(1,number_of_authors+1,1):
            authors.append(list[itr])
        if(number_of_authors==1):
            author = str(authors[0])

            t1 = threading.Thread(target=profiling1, args=(author, keywords))

            # t1 = profiling1(author,keywords)
            t1.start()
            t1.join()

            final_output = json.dumps({"t1": author_profiles[0]})
            final_output = json.loads(final_output)
            return Response(final_output)   
        
        elif(number_of_authors==2):
            author1 = str(authors[0])
            author2 = str(authors[1])
            
            t1 = threading.Thread(target=profiling1,args=(author1,keywords))
            t2 = threading.Thread(target=profiling1,args=(author2,keywords))
        
            t1.start()
            t2.start()
            
            t1.join()
            t2.join()
            
            final_output = json.dumps({"t1": author_profiles[0], "t2": author_profiles[1]})
            final_output = json.loads(final_output)
            return Response(final_output)

        else:
            author1 = str(authors[0])
            author2 = str(authors[1])
            author3 = str(authors[2])
            
            t1 = threading.Thread(target=profiling1,args=(author1,keywords))
            t2 = threading.Thread(target=profiling1,args=(author2,keywords))
            t3 = threading.Thread(target=profiling1,args=(author3,keywords))
        
            t1.start()
            t2.start()
            t3.start()

            time.sleep(30)

            t1.join()
            t2.join()
            t3.join()
            
            final_output = json.dumps({"t1": author_profiles[0], "t2": author_profiles[1], "t3": author_profiles[2]})
            final_output = json.loads(final_output)
            return Response(final_output)
    return Response()

# print(authorProfiling(["image theory analysis and image","https://ieeexplore.ieee.org/author/37283451200", "https://ieeexplore.ieee.org/author/37086061607", "https://ieeexplore.ieee.org/author/37085753500"]))
# * Dr. Antriksh Goswami Sir : https://ieeexplore.ieee.org/author/37086061607
# * Dr. Novarun Deb Sir : https://ieeexplore.ieee.org/author/37085753500
# * Dr. Sunil Dutt Sir : https://ieeexplore.ieee.org/author/37085562899
# * Alan Bovik : https://ieeexplore.ieee.org/author/37283451200
# * Muhammad Alrabeiah : https://ieeexplore.ieee.org/author/37086822595

