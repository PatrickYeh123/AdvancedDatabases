# Feb 19
# psy2107

import sys
import string
import pprint
from itertools import permutations
import json
from googleapiclient.discovery import build


def remove_punctuation(test_str):
    # Using filter() and lambda function to filter out punctuation characters
    result = ''.join(filter(lambda x: x.isalpha() or x.isdigit() or x.isspace(), test_str))
    return result

def main(stop_words):
    # Build a service object for interacting with the API. Visit
    # the Google APIs Console <http://code.google.com/apis/console>
    # to get an API key for your own application.
    clientKey = "xyz"
    engineKey = "xyz"
    service = build(
        "customsearch", "v1", developerKey=clientKey
    )


    # Get user input: query and desired precision@10
    precision = float(input('What is your desired prec@10? (Enter a value in [0, 1]) '))
    queryTokens = []
    query = input('What is your desired query? ')
    query = query.lower()
    queryTokens = query.split()
    firstIteration = True


    while True:
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

        # Debug
        #print('********************')
        #pprint.pprint(res)
        #print('********************')
        
        #TODO: Check doc type: fileFormat key exists iff non-HTML
        topTen = res['items'][:10]

        relevant = []
        irrelevant = []

        print('Parameters:')
        print('Client key  = ' + clientKey)
        print('Engine key  = ' + engineKey)
        print('Query       = ' + query)
        print('Precision   = ' + str(precision))
        print('Google Search Results:')
        print('======================')
        for i in range(10):
            print('Result ' + str(i+1))
            print('[')
            print(' URL: ' + topTen[i]['formattedUrl'])
            print(' Title: ' + topTen[i]['title'])
            print(' Summary: ' + topTen[i]['snippet'])
            print(']')

            feedback = input('Relevant (Y/N)? ')
            feedback.lower()
            if feedback == 'y':
                relevant.append(topTen[i])
            else:
                irrelevant.append(topTen[i])

        # print('Here are the relevant entries:')
        # for x in relevant:
        #     print(x['title'])
                
        currPrec = len(relevant) / 10
        print('======================')
        print('FEEDBACK SUMMARY')
        print('Query ' + query)
        print('Precision ' + str(currPrec))

        if currPrec == 0:
            print('Precision was 0! Done.')
            break
        elif currPrec < precision:
            print('Still below the desired precision of ' + str(precision))

            # index results: add <= 2 key words
            freqs = {}
            relevantCorpus = ""

            ir_freqs = {}
            ir_corpus = ""

            for doc in relevant:
                title = doc['title']
                summary = doc['snippet']

                title = remove_punctuation(title)
                title = title.lower()
                titleWords = title.split()

                summary = remove_punctuation(summary)
                summary = summary.lower()
                summaryWords = summary.split()

                relevantCorpus += "|| " + title + " " + summary + " ||" 

                for word in titleWords:
                    if word in freqs:
                        freqs[word] += 1
                    else:
                        freqs.update({word : 1})

                for word in summaryWords:
                    if word in freqs:
                        freqs[word] += 1
                    else:
                        freqs.update({word : 1})


            for doc in irrelevant:
                title = doc['title']
                summary = doc['snippet']

                title = remove_punctuation(title)
                title = title.lower()
                titleWords = title.split()

                summary = remove_punctuation(summary)
                summary = summary.lower()
                summaryWords = summary.split()

                ir_corpus += "|| " + title + " " + summary + " ||" 

                # note: we will only penalize for one irrelevant doc, not all of them
                for word in titleWords:
                    # Essentially, penalize for appearing in irrelevant docs
                    if word in freqs:
                        freqs[word] -= 1
                    elif word in ir_freqs:
                        ir_freqs[word] += 1
                    else:
                        ir_freqs.update({word : 1})
                    break

                for word in summaryWords:
                    if word in freqs:
                        freqs[word] -= 1
                    elif word in ir_freqs:
                        ir_freqs[word] += 1
                    else:
                        freqs.update({word : 1})
                    break

            # print('DEBUG: dictionary counts')
            freqs_sorted = sorted(freqs.items(), key=lambda x: x[1], reverse=True)
            #for keyVal in freqs_sorted:
               # print(keyVal[0] + ' : ' + str(keyVal[1]))
            
            clear = '\''

            augmentations = []
            for i in freqs_sorted:
                if i[0] not in stop_words and i[0] not in queryTokens:
                    augmentations.append(i[0])
                    if len(augmentations) >= 2:
                        break

            # augment query by adding new words
            for i in augmentations:
                print('Augmenting query by ' + i)
                queryTokens.append(i)

            # Main logic: try different permutations and evaluate the bigram results
            orderings = list(permutations(range((len(queryTokens)))))
            # print('Orderings: ')
            # print(orderings)

            bestScore = 0
            bestOrder = queryTokens

            for order in orderings:
                new_query = []
                for i in list(range(len(queryTokens))):
                    new_query.append(queryTokens[order[i]])
                # print('One permutation:')
                # print(new_query)

                # assign a score to this permutation
                # if it is better than previous best, then update
                score = 0
                for i in list(range(len(queryTokens) - 1)):
                    substr = new_query[i] + " " + new_query[i+1]
                    score += relevantCorpus.count(substr)
                if score > bestScore:
                    bestScore = score
                    bestOrder = new_query
                # print('One score:')
                # print(score)

            print('Computed best order: ' + str(bestOrder))

            queryTokens = bestOrder

            query = ""
            for token in queryTokens:
                query += token + " "
        else:
            print('Desired precision reached. Done.')
            break      





if __name__ == "__main__":
    # list of stop words acquired from class page
    # put here and parametrized the main function to remove clutter
    stop_words = ['a', 'ii', 'about', 'above', 'according', 'across', '39', 'actually', 'ad', 'adj', 'ae', 'af', 'after', 'afterwards', 'ag', 'again', 'against', 'ai', 'al', 'all', 'almost', 'alone', 'along', 'already', 'also', 'although', 'always', 'am', 'among', 'amongst', 'an', 'and', 'another', 'any', 'anyhow', 'anyone', 'anything', 'anywhere', 'ao', 'aq', 'ar', 'are', 'aren', "aren't", 'around', 'arpa', 'as', 'associate', 'at', 'au', 'aw', 'az', 'b', 'ba', 'bb', 'bd', 'be', 'became', 'because', 'become', 'becomes', 'becoming', 'been', 'before', 'beforehand', 'begin', 'beginning', 'behind', 'being', 'below', 'beside', 'besides', 'between', 'beyond', 'bf', 'bg', 'bh', 'bi', 'billion', 'bj', 'bm', 'bn', 'bo', 'both', 'br', 'bs', 'bt', 'but', 'buy', 'bv', 'bw', 'by', 'bz', 'c', 'ca', 'can', "can't", 'cannot', 'caption', 'cc', 'cd', 'cf', 'cg', 'ch', 'ci', 'ck', 'cl', 'click', 'cm', 'cn', 'co', 'co.', 'com', 'copy', 'could', 'couldn', "couldn't", 'cr', 'cs', 'cu', 'cv', 'cx', 'cy', 'cz', 'd', 'de', 'did', 'didn', "didn't", 'dj', 'dk', 'dm', 'do', 'does', 'doesn', "doesn't", 'don', "don't", 'down', 'during', 'dz', 'e', 'each', 'ec', 'edu', 'ee', 'eg', 'eh', 'eight', 'eighty', 'either', 'else', 'elsewhere', 'end', 'ending', 'enough', 'er', 'es', 'et', 'etc', 'even', 'ever', 'every', 'everyone', 'everything', 'everywhere', 'except', 'f', 'few', 'fi', 'fifty', 'find', 'first', 'five', 'fj', 'fk', 'fm', 'fo', 'for', 'former', 'formerly', 'forty', 'found', 'four', 'fr', 'free', 'from', 'further', 'fx', 'g', 'ga', 'gb', 'gd', 'ge', 'get', 'gf', 'gg', 'gh', 'gi', 'gl', 'gm', 'gmt', 'gn', 'go', 'gov', 'gp', 'gq', 'gr', 'gs', 'gt', 'gu', 'gw', 'gy', 'h', 'had', 'has', 'hasn', "hasn't", 'have', 'haven', "haven't", 'he', "he'd", "he'll", "he's", 'help', 'hence', 'her', 'here', "here's", 'hereafter', 'hereby', 'herein', 'hereupon', 'hers', 'herself', 'him', 'himself', 'his', 'hk', 'hm', 'hn', 'home', 'homepage', 'how', 'however', 'hr', 'ht', 'htm', 'html', 'http', 'hu', 'hundred', 'i', "i'd", "i'll", "i'm", "i've", 'i.e.', 'id', 'ie', 'if', 'il', 'im', 'in', 'inc', 'inc.', 'indeed', 'information', 'instead', 'int', 'into', 'io', 'iq', 'ir', 'is', 'isn', "isn't", 'it', "it's", 'its', 'itself', 'j', 'je', 'jm', 'jo', 'join', 'jp', 'k', 'ke', 'kg', 'kh', 'ki', 'km', 'kn', 'kp', 'kr', 'kw', 'ky', 'kz', 'l', 'la', 'last', 'later', 'latter', 'lb', 'lc', 'least', 'less', 'let', "let's", 'li', 'like', 'likely', 'lk', 'll', 'lr', 'ls', 'lt', 'ltd', 'lu', 'lv', 'ly', 'm', 'ma', 'made', 'make', 'makes', 'many', 'maybe', 'mc', 'md', 'me', 'meantime', 'meanwhile', 'mg', 'mh', 'microsoft', 'might', 'mil', 'million', 'miss', 'mk', 'ml', 'mm', 'mn', 'mo', 'more', 'moreover', 'most', 'mostly', 'mp', 'mq', 'mr', 'mrs', 'ms', 'msie', 'mt', 'mu', 'much', 'must', 'mv', 'mw', 'mx', 'my', 'myself', 'mz', 'n', 'na', 'namely', 'nc', 'ne', 'neither', 'net', 'netscape', 'never', 'nevertheless', 'new', 'next', 'nf', 'ng', 'ni', 'nine', 'ninety', 'nl', 'no', 'nobody', 'none', 'nonetheless', 'noone', 'nor', 'not', 'nothing', 'now', 'nowhere', 'np', 'nr', 'nu', 'nz', 'o', 'of', 'off', 'often', 'om', 'on', 'once', 'one', "one's", 'only', 'onto', 'or', 'org', 'other', 'others', 'otherwise', 'our', 'ours', 'ourselves', 'out', 'over', 'overall', 'own', 'p', 'pa', 'page', 'pe', 'per', 'perhaps', 'pf', 'pg', 'ph', 'pk', 'pl', 'pm', 'pn', 'pr', 'pt', 'pw', 'py', 'q', 'qa', 'r', 'rather', 're', 'recent', 'recently', 'reserved', 'ring', 'ro', 'ru', 'rw', 's', 'sa', 'same', 'sb', 'sc', 'sd', 'se', 'seem', 'seemed', 'seeming', 'seems', 'seven', 'seventy', 'several', 'sg', 'sh', 'she', "she'd", "she'll", "she's", 'should', 'shouldn', "shouldn't", 'si', 'since', 'site', 'six', 'sixty', 'sj', 'sk', 'sl', 'sm', 'sn', 'so', 'some', 'somehow', 'someone', 'something', 'sometime', 'sometimes', 'somewhere', 'sr', 'st', 'still', 'stop', 'su', 'such', 'sv', 'sy', 'sz', 't', 'taking', 'tc', 'td', 'ten', 'tells', 'text', 'tf', 'tg', 'test', 'th', 'than', 'that', "that'll", "that's", 'the', 'their', 'them', 'themselves', 'then', 'thence', 'there', "there'll", "there's", 'thereafter', 'thereby', 'therefore', 'therein', 'thereupon', 'these', 'they', "they'd", "they'll", "they're", "they've", 'thirty', 'this', 'those', 'though', 'thousand', 'three', 'through', 'throughout', 'thru', 'thus', 'tj', 'tk', 'tm', 'tn', 'to', 'together', 'too', 'toward', 'towards', 'tp', 'tr', 'trillion', 'tt', 'tv', 'tw', 'twenty', 'two', 'tz', 'u', 'ua', 'ug', 'uk', 'um', 'under', 'unless', 'unlike', 'unlikely', 'until', 'up', 'upon', 'us', 'use', 'used', 'using', 'uy', 'uz', 'v', 'va', 'vc', 've', 'very', 'vg', 'vi', 'via', 'vn', 'vu', 'w', 'was', 'wasn', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'web', 'webpage', 'website', 'welcome', 'well', 'were', 'weren', "weren't", 'wf', 'what', "what'll", "what's", 'whatever', 'when', 'whence', 'whenever', 'where', 'whereafter', 'whereas', 'whereby', 'wherein', 'whereupon', 'wherever', 'whether', 'which', 'while', 'whither', 'who', "who'd", "who'll", "who's", 'whoever', 'NULL', 'whole', 'whom', 'whomever', 'whose', 'why', 'will', 'with', 'within', 'without', 'won', "won't", 'would', 'wouldn', "wouldn't", 'ws', 'www', 'x', 'y', 'ye', 'yes', 'yet', 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves', 'yt', 'yu', 'z', 'za', 'zm', 'zr', '10', 'z', 'href']
    main(stop_words)

