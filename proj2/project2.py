import sys
import string
import pprint
from itertools import permutations
import json
from googleapiclient.discovery import build

from bs4 import BeautifulSoup
import urllib.parse
import urllib.request
import requests

import spacy
from spacy_help_functions import get_entities, create_entity_pairs


# Load pre-trained SpanBERT model
from spanbert import SpanBERT

import os
import google.generativeai as genai
import time

# Apply Gemini API Key
GEMINI_API_KEY = 'AIzaSyBbOpPrCbS0_kM0Z1PIp2t3SLQKee4Wqv0'  # Substitute your own key here
genai.configure(api_key=GEMINI_API_KEY)

# Generate response to prompt
def get_gemini_completion(prompt, model_name, max_tokens, temperature, top_p, top_k):

    # Initialize a generative model
    model = genai.GenerativeModel(model_name)

    # Configure the model with your desired parameters
    generation_config=genai.types.GenerationConfig(
        max_output_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k
    )

    # Generate a response
    response = model.generate_content(prompt, generation_config=generation_config)
    #print('waiting...')
    time.sleep(1.8)

    return response.text

def remove_punctuation(test_str):
    # Using filter() and lambda function to filter out punctuation characters
    result = ''.join(filter(lambda x: x.isalpha() or x.isdigit() or x.isspace(), test_str))
    return result

def main():
    # TODO: filter entities of interest based on target relation
    entities_of_interest = ["ORGANIZATION", "PERSON", "LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]

    # Load spacy model
    nlp = spacy.load("en_core_web_lg")


    # Build a service object for interacting with the API. Visit
    # the Google APIs Console <http://code.google.com/apis/console>
    # to get an API key for your own application.
    clientKey = "AIzaSyBOskhE799tyaHkMxJc08i3YLZiJj6vubw"
    engineKey = "10e635b85174848d2"
    service = build(
        "customsearch", "v1", developerKey=clientKey
    )

    # Gemini API key
    geminiKey = "AIzaSyBbOpPrCbS0_kM0Z1PIp2t3SLQKee4Wqv0"

    #print ('argument list', sys.argv)
    is_spanbert = False
    if sys.argv[1] == '-spanbert':
        is_spanbert = True
        spanbert = SpanBERT("./pretrained_spanbert")
    r = int(sys.argv[5]) # 1 - schools 2 - works for 3 - lives in 4 - top member employees
    t = float(sys.argv[6])
    query = sys.argv[7]
    k = int(sys.argv[8])
    querySet = set()
    querySet.add(query)


    #print("SpanBERT:", spanbert)
    #print("Google API Key:", clientKey)
    #print("Engine ID:", engineKey)
    #print("Gemini API Key:", geminiKey)
    #print("r:", r)
    #print("t:", t)
    #print("q:", query)
    #print("k:", k)

    
    firstIteration = True

    X = dict()
    listX = []
    seenURL = set()

    iterats = 0

    # print intro message
    print('____')
    print('Parameters:')
    print('Client key	= ' + clientKey)
    print('Engine key	= ' + engineKey)
    print('Gemini key	= ' + geminiKey)
    methodName = 'spanbert'
    if not is_spanbert:
        methodName = 'gemini'
    print('Method	= ' + methodName)
    relation_names = ["Schools_Attended", "Work_For", "Live_In", "Top_Member_Employees"]
    print('Relation	= ' + relation_names[r-1])
    print('Threshold	= ' + str(t))
    print('Query		= ' + query)
    print('# of Tuples	= ' + str(k))
    print('Loading necessary libraries; This should take a minute or so ...)')


    total_relations = 0
    while True:
        print('=========== Iteration: ' + str(iterats) + ' - Query: ' + query + ' ===========')

        # Main feedback loop: query, get relevance from user, mark prec@10, update
        res = (
            service.cse()
            .list(
                q=query,
                cx=engineKey,
            )
            .execute()
        )

        if 'items' not in res.keys() or (firstIteration and len(res['items']) < 10):
            print('Not enough results from first query, ending program.')
            break
        
        firstIteration = False

        topTen = res['items'][:10]

        print('Google Search Results:')
        print('======================')
        for i in range(10):
            local_relations = 0
            print('URL ( ' + str(i+1) + ' / 10): ' + topTen[i]['link'])
            link = topTen[i]['link']
            if link in seenURL:
                print('This link was already seen!')
                continue
            seenURL.add(link)

            url = link
            #html = urllib.request.urlopen(url).read()
            print('Fetching text from url ...')
            try:
                html = requests.get(url, timeout=10).text
            except Timeout:
                print('Request timed out. Moving to next item.')
                continue

            soup = BeautifulSoup(html, features="html.parser")

            # kill all script and style elements
            for script in soup(["script", "style"]):
                script.extract()    # rip it out

            # get text
            text = soup.get_text(' ', strip=True)
            #text = soup.get_text()

            # break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)

            raw_text = text
            if len(text) > 10000:
                print('Trimming webpage content from ' + str(len(text)) + ' to 10000 characters')
                raw_text = text[:10000]
            print('Webpage length (num characters): ' + str(len(raw_text)))
            
            # Apply spacy model to raw text (to split to sentences, tokenize, extract entities etc.)
            print('Annotating the webpage using spacy...')
            doc = nlp(raw_text)

            total_num_sents = 0
            for sentence in doc.sents:
                total_num_sents += 1
            print('Extracted ' + str(total_num_sents) + ' sentences. Processing each sentence one by one to check for presence of right pair of named entity types; if so, will run the second pipeline ...')
            num_sents = 0
            annotations_extracted = 0
            for sentence in doc.sents:
                num_sents += 1
                if num_sents % 5 == 0:
                    print('Processed ' + str(num_sents) + ' / ' + str(total_num_sents) + ' sentences')

                #print("\n\nProcessing sentence: {}".format(sentence))
                #print("Tokenized sentence: {}".format([token.text for token in sentence]))
                ents = get_entities(sentence, entities_of_interest)
                #print("spaCy extracted entities: {}".format(ents))

                # create entity pairs
                candidate_pairs = []
                sentence_entity_pairs = create_entity_pairs(sentence, entities_of_interest)
                for ep in sentence_entity_pairs:
                    # TODO: keep subject-object pairs of the right type for the target relation (e.g., Person:Organization for the "Work_For" relation)
                    if r == 1 or r == 2:
                        # 1. schools attended: subj:PERSON obj:ORGANIZATION
                        # 2. work for: subj:PERSON obj:ORGANIZATION
                        if ep[1][1] == 'PERSON' and ep[2][1] == 'ORGANIZATION':
                            # e1=Subject, e2=Object
                            candidate_pairs.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})  
                        if ep[2][1] == 'PERSON' and ep[1][1] == 'ORGANIZATION':
                            # e1=Object, e2=Subject
                            candidate_pairs.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})  

                    elif r == 3:
                        # 3. live in: subj:PERSON obj: one of LOCATION, CITY, STATE_OR_PROVINCE, or COUNTRY
                        if ep[1][1] == 'PERSON' and (ep[2][1] == entities_of_interest[2] or ep[2][1] == entities_of_interest[3] or ep[2][1] == entities_of_interest[4] or ep[2][1] == entities_of_interest[5]):
                            # e1=Subject, e2=Object
                            candidate_pairs.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})  
                        if ep[2][1] == 'PERSON' and (ep[1][1] == entities_of_interest[2] or ep[1][1] == entities_of_interest[3] or ep[1][1] == entities_of_interest[4] or ep[1][1] == entities_of_interest[5]):
                            # e1=Object, e2=Subject
                            candidate_pairs.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})  

                    else:
                        # 4. top member employees: subj:ORGANIZATION obj: PERSON
                        if ep[2][1] == 'PERSON' and ep[1][1] == 'ORGANIZATION':
                            # e1=Subject, e2=Object
                            candidate_pairs.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})  
                        if ep[1][1] == 'PERSON' and ep[2][1] == 'ORGANIZATION':
                            # e1=Object, e2=Subject
                            candidate_pairs.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})  

                    #candidate_pairs.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})  # e1=Subject, e2=Object
                    #candidate_pairs.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})  # e1=Object, e2=Subject


                # Classify Relations for all Candidate Entity Pairs using SpanBERT
                candidate_pairs = [p for p in candidate_pairs if not p["subj"][1] in ["DATE", "LOCATION"]]  # ignore subject entities with date/location type
                #print("Candidate entity pairs:")
                #for p in candidate_pairs:
                    #print("Subject: {}\tObject: {}".format(p["subj"][0:2], p["obj"][0:2]))

                if len(candidate_pairs) == 0:
                    #print('skipping!')
                    continue
                annotations_extracted += 1

                if is_spanbert:
                    #print("Applying SpanBERT for each of the {} candidate pairs. This should take some time...".format(len(candidate_pairs)))
                    relation_preds = spanbert.predict(candidate_pairs)  # get predictions: list of (relation, confidence) pairs
                else:
                    prompt_text = """Given a sentence, extract all the (subject, object) relations satisfying our intended relation. Output a list of (subject, object) tuples, one tuple per line, with the subject and object separated by a semicolon.
                    Here are the four relations:
                    Schools_Attended: Subject: PERSON, Object: ORGANIZATION (i.e. "Joe Smith;Harvard" where the subject "Joe Smith" attended Harvard, which is a school)
                    Work_For: Subject: PERSON, Object: ORGANIZATION (i.e. "Joe Smith;Apple" where the subject "Joe Smith" works for the organization Apple, which is a company or entity)
                    Live_In: Subject: PERSON, Object: one of LOCATION, CITY, STATE_OR_PROVINCE, or COUNTRY (i.e. "Bill Gates; Seattle" where the subject "Bill Gates" has lived in the object "Seattle", which is a place)
                    Top_Member_Employees: Subject: ORGANIZATION, Object: PERSON (i.e. "Apple;Tim Cook" where the subject "Apple" is an organization and the object "Tim Cook" is a high-ranking or important employee, in this case the CEO, for that organization)
                    """

                    relation_names = ["Schools_Attended", "Work_For", "Live_In", "Top_Member_Employees"]
                    relation_explanations = ["", "the first portion of the tuple is a person and the second part is the organization that person has worked for. ", "", ""]

                    prompt_text += "We will use the " + relation_names[r-1] + " relation, which means " + relation_explanations[r-1]

                    prompt_text += "Here is the sentence, please extract all possible tuples from it: "
                    #sentence = """Bill Gates stepped down as chairman of Microsoft in February 2014 and assumed a new post as technology adviser to support the newly appointed CEO Satya Nadella. """
                    prompt_text += str(sentence)

                    prompt_text += "extracted:"

                    # Feel free to modify the parameters below.
                    # Documentation: https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini
                    model_name = 'gemini-pro'
                    max_tokens = 100
                    temperature = 0.2
                    top_p = 1
                    top_k = 32

                    response_text = get_gemini_completion(prompt_text, model_name, max_tokens, temperature, top_p, top_k)
                    #print("**** RESPONSE FROM GEMINI ****")
                    #print(response_text)
                    response_text = response_text.split('\n')
                    for entry in response_text:
                        entry = entry.split(';')
                        if len(entry) < 2:
                            continue
                        keyV = (entry[0], entry[1])
                        print('=== Extracted Relation ===')
                        print('Sentence: ' + str(sentence))
                        print('Subject: ' + str(keyV[0]) + ' ; Object: ' + str(keyV[1]) + ' ;')
                        if keyV in X:
                            print('Duplicate. Ignoring this.')
                        else:
                            local_relations += 1
                            total_relations += 1
                            print('Adding to set of extracted relations')
                        X[keyV] = 1
                        print('==========')
                        #print(keyV)


                # Print Extracted Relations
                #print("\nExtracted relations:")
                if is_spanbert:
                    for ex, pred in list(zip(candidate_pairs, relation_preds)):
                        can_add = False
                        if r == 1 and pred[0] == 'per:schools_attended':
                            #print("\tSubject: {}\tObject: {}\tRelation: {}\tConfidence: {:.2f}".format(ex["subj"][0], ex["obj"][0], pred[0], pred[1]))
                            can_add = True

                        elif r == 2 and pred[0] == 'per:employee_of':
                            #print("\tSubject: {}\tObject: {}\tRelation: {}\tConfidence: {:.2f}".format(ex["subj"][0], ex["obj"][0], pred[0], pred[1]))
                            can_add = True

                        elif r == 3 and pred[0] == 'per:cities_of_residence':
                            #print("\tSubject: {}\tObject: {}\tRelation: {}\tConfidence: {:.2f}".format(ex["subj"][0], ex["obj"][0], pred[0], pred[1]))
                            can_add = True

                        elif r == 4 and pred[0] == 'org:top_members/employees':
                            #print("\tSubject: {}\tObject: {}\tRelation: {}\tConfidence: {:.2f}".format(ex["subj"][0], ex["obj"][0], pred[0], pred[1]))
                            can_add = True

                        if can_add:
                            if is_spanbert and pred[1] >= t:
                                print('=== Extracted Relation ===')
                                sentence_tokens = [token.text for token in sentence]
                                print('Input tokens: ' + str(sentence_tokens))

                                keyV = (ex['subj'][0], ex['obj'][0])
                                print('Confidence: ' + str(pred[1]) + ' ; Subject: ' + ex['subj'][0] + ' ; Object: ' + ex['obj'][0])
                                if keyV not in X or X[keyV] < pred[1]:
                                    X[keyV] = pred[1]
                                    local_relations += 1
                                    total_relations += 1
                                    print('Added or updated to the set!')
                                else:
                                    print('Confidence was too low or lower than a previous duplicate entry')



                    # TODO: focus on target relations
                    # '1':"per:schools_attended"
                    # '2':"per:employee_of"
                    # '3':"per:cities_of_residence"
                    # '4':"org:top_members/employees"
            print('Annotations extracted for ' + str(annotations_extracted) + ' out of ' + str(total_num_sents) + ' sentences.')
            print('Relations added/updated: ' + str(local_relations) + ' out of ' + str(total_relations) + ' total')

            #print(text[:10000])


            #print(' URL: ' + topTen[i]['formattedUrl'])

        iterats += 1
        if is_spanbert:
            listX = sorted(list(X.items()), key=lambda x: (-x[1], x[0]))[:k]
        else:
            listX = sorted(list(X.items()), key=lambda x: (-x[1], x[0]))

        if len(X) >= k or iterats > 3:
            print('================== TOP RELATIONS =================')
            print('Relation: ' + relation_names[r-1])
            print('(Ignore if Gemini) For k = ' + str(k))
            for entry in listX:
                print('Confidence: ' + str(entry[1]) + ' | Subject: ' + entry[0][0] + ' | Object: ' + entry[0][1])
            print('Total # of iterations = ' + str(iterats))
            return

        # TODO: get a new query if we haven't reached our goal yet
        queryFound = False
        for i in listX:
            newQuery = i[0][0] + ' ' + i[0][1]
            newQuery = newQuery.lower()

            if newQuery not in querySet:
                querySet.add(newQuery)
                query = newQuery
                print('New query is: ' + query)
                queryFound = True
                break

        if not queryFound:
            print('ISE has stalled')
            return



if __name__ == "__main__":
    main()
