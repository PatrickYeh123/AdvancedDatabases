'''
Patrick Yeh (psy2107)
Sameer Saxena
COMS 6111 Advanced Databases Project 3
'''
import sys
# combos needed to iterate through different ways to select/expand sets in the a priori algorithm
from itertools import combinations 
import csv


def get_curr_basket_powerset(next_basket_powerset, k):
    prev_sets = set()

    # get the previous sets
    for candidate_basket in next_basket_powerset:
        prev_sets.add(candidate_basket)

    curr_basket_powerset = dict()
    for tup in dataset:
        candidate_set = set()
        for i in combinations(tup, k):
            candidate_set.add(tuple(sorted(i)))

        for other_set in candidate_set.intersection(prev_sets):
            if other_set not in curr_basket_powerset:
                curr_basket_powerset[other_set] = 1
            else:
                curr_basket_powerset[other_set] += 1
    
    # check if support is valid or not
    curr_basket_powerset_list = [ ]
    for other_set in sorted(curr_basket_powerset.keys()):
        curr_sup = curr_basket_powerset[other_set] / n
        if curr_sup >= min_sup:
            baskets[other_set] = curr_sup
            curr_basket_powerset_list.append(other_set)

    return curr_basket_powerset_list


def expand_basket(curr_basket_powerset, k):
    next_basket_powerset = [ ]

    # get the previous baskets to construct the new ones
    prev_set = set(curr_basket_powerset)

    # TODO: can we optimize?
    # Answer: yes, using paper
    
    # use k_shift to make indexing of k more logical
    # i.e. we are dealing wrt the previous baskets with size k' = k - 1
    k_shift = k - 1

    # join two tuples P and Q according to the apriori algorithm
    # keep an order to avoid duplicates
        
    # iterate through all possible ways to combine the two P and Q
    for P, Q in combinations(curr_basket_powerset, 2):
        # P and Q agree on all but the last item
        if P[ : k_shift - 2] == Q[ : k_shift - 2]:
            new_tup = list(P)
            # Add the last item of Q to make the new tuple 
            new_tup.append(Q[k_shift - 1])
            # maintain a sorted order of the baskets to avoid duplicates
            next_basket_powerset.append(tuple(sorted(new_tup))) 

    # 'in the prune step, we delete all baskets c in ck
    # 'such that some (k-1)-subset of c is not in Lk-1'
    # - taken from the apriori paper
    for basket_candidate in next_basket_powerset:
        for item in combinations(basket_candidate, k - 1):
            # delete if this is the case
            if item not in prev_set:
                next_basket_powerset.remove(basket_candidate)
                break

    return next_basket_powerset


def get_initial_basket():
    # extract all large baskets with size of 1 and calculate the support metric
    initial_basket = [ ]
    # map an individual item to its frequency, to get the support
    freqs = dict()
    
    for tup in dataset:
        for obj in tup:
            # skip if the attribute/basket object does not exist
            # else, increment counts to get the support
            if len(obj) == 0:
                continue
            elif obj not in freqs:
                # initialize with 0 before incrementing to 1
                freqs[obj] = 0

            freqs[obj] += 1
    
    # perform the support calculation
    for obj in sorted(freqs.keys()):
        curr_sup = float(freqs[obj]) / n
        # only add to our set if we meet the minimum threshold
        if curr_sup >= min_sup:
            # use (obj,) to make sure it is treated as a tuple
            # this is to key correctly for the baskets dictionary
            tup = (obj,)
            baskets[tup] = curr_sup
            initial_basket.append(tup)
        else:
            # simply discard an attribute if it doesn't meet the threshold
            # corresponds to the a priori assumption
            freqs.pop(obj)

    return initial_basket


def run_apriori():
    # step 1: initialize
    curr_basket_powerset = get_initial_basket()

    # step 2: for k = 2 onwards, iteratively expand baskets
    k = 2

    # repeat until we can no longer grow our baskets
    while len(curr_basket_powerset) > 0:
        # get the next iteration's sets by expanding
        next_basket_powerset = expand_basket(curr_basket_powerset, k)
        # set the current set of sets to the new one
        curr_basket_powerset = get_curr_basket_powerset(next_basket_powerset, k)
        # increment size of our sets
        k = k + 1


def create_implications():
    # find implications that match our criteria (i.e. meet the min_conf level)
    implications = dict()
    for basket in baskets.keys():
        # no one item implications (i.e. both sides must be nonempty)
        if len(basket) == 1:
            continue

        # iterate through each item as the righthand singleton set
        for singleton_item in basket:
            left = list(basket)
            left.remove(singleton_item)
            left_sup = baskets[tuple(left)]

            # apriori: if left support is zero, no need
            if left_sup > 0:
                total_sup = baskets[basket]


                conf_implication = total_sup / left_sup

                singleton_set = [singleton_item]
                
                if conf_implication >= min_conf:
                    # use sup_conf to map the implication to its metrics
                    sup_conf = dict()
                    sup_conf['sup'] = baskets[basket]
                    sup_conf['conf'] = conf_implication

                    # implication has form [basket set] => [singleton item]

                    basketset_str = '[' + ','.join(left) + ']'
                    singleton_str = '[' + str(singleton_set[0]) + ']'
                    implication_str = basketset_str + ' => ' + singleton_str

                    implications[implication_str] = sup_conf
    
    return implications


def print_out():
    transcript_file = open('output.txt', 'w')

    # write baskets into file
    str1 = ' ========== Frequent itemsets (min_sup=' + str(100 * min_sup) + '%) ============================================================ '
    print(str1)
    transcript_file.write(str1 + '\n')

    # sort the sets in decreasing order of support
    market_baskets_sup_decr = sorted(baskets.items(), key = lambda x: x[1], reverse = True)
    for basket in market_baskets_sup_decr:
        str2 = '[' + ','.join(basket[0]) + '], ' + str(100 * basket[1]) + '%'
        print(str2)
        transcript_file.write(str2 + '\n')

    str3 = ' ========== High-confidence association rules (min_conf=' + str(100 * min_conf) + '%) ================================================== '
    print(str3)
    transcript_file.write(str3 + '\n')
    for implication in implications_conf_decr:
        str4 = implication[0] + ' (Conf: ' + str(100 * implication[1]['conf']) + '%  Supp: ' + str(100 * implication[1]['sup']) + '%)'
        print(str4)
        transcript_file.write(str4 + '\n')

    transcript_file.close()


if __name__ == "__main__":
    # read command line arguments
    # 'python3 proj3.py src.csv min_sup min_conf'
    src_csv = str(sys.argv[1])
    # open and read csv into attribute tuples
    src_file = open(src_csv, 'r')
    src_data = [tuple(sample) for sample in csv.reader(src_file)]
    
    min_sup = float(sys.argv[2])
    min_conf = float(sys.argv[3])

    # store all the attribute tuples into a set for fast access
    dataset = set()
    for tup in src_data:
        dataset.add(tup)

    # number of tuples in dataset
    n = len(dataset)
    
    # maps an basket to its corresponding support
    baskets = dict()

    # Run apriori
    # populate the baskets
    run_apriori()

    # get the implications from a priori algorithm
    implications = create_implications()

    # sort in decreasing order of confidence
    implications_conf_decr = sorted(implications.items(), key = lambda x: x[1]['conf'], reverse = True)

    # print and write the outputs
    print_out()


