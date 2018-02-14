# import os
# import dpath.util as dpu
#
# print(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')))
# dirname, filename = os.path.split(os.path.abspath(__file__))
# print(dirname)

# d={
#     "wells":{
#         "9815":{
#             "gor":1000
#         },
#         "15":{
#             "gor":1000
#         }
#     }
# }
#
# print(d)
#
# r=dpu.set(d, 'wells/**/gor',0)
# print(r)
# print(d)

import numpy as np
import sys
from matplotlib import pyplot as plt



def survive(wells,dna,data,tls):
    avg_gor=0.0
    col=[]
    score=0.0
    for tl in tls:
        tl_cnt=0.0
        gor=0.0
        c=[]
        for i,d in enumerate(dna):
            if d==tl:
                gor+=data[wells[i]]["g"]
                tl_cnt+=1
                c.append(data[wells[i]]["g"])
        col.append(c)
        if tl_cnt:
            avg_gor=gor/tl_cnt

        if avg_gor>0.0:
            score+=abs(avg_gor-500.0)

    return score,col


def qc(tls,dna):
    col=[]
    for tl in tls:
        c=[]
        for i,d in enumerate(dna):
            if d==tl:
                c.append(data[wells[i]]["g"])
        col.append(c)
    return col

def make_population(n,t):
    population=[]
    p=0
    while p<n:
        rand_route=[]
        for well in wells:
            rand_route.append(data[well]["r"][np.random.randint(t)])

        flag=0
        col=qc(tls,rand_route)
        for c in col:
            if not c:
                flag=1

        if flag==0:
            population.append(rand_route)
        else:
            p-=1
        p+=1

    return population

if __name__=="__main__":

    tls=["a","b","c","d","e"]

    data={

        "w2":{"g":10.0,"r":["a","b","c","d","e"]},
        "w3":{"g":500.0,"r":["a","b","c","d","e"]},
        "w4":{"g":350.0,"r":["a","b","c","d","e"]},
        "w5":{"g":150.0,"r":["a","b","c","d","e"]},
        "w7":{"g":1500.0,"r":["a","b","c","d","e"]},
        "w9":{"g":750.0,"r":["a","b","c","d","e"]},
        "w10":{"g":900.0,"r":["a","b","c","d","e"]},
        "w11":{"g":800.0,"r":["a","b","c","d","e"]},
        "w13":{"g":1200.0,"r":["a","b","c","d","e"]},
        "w14":{"g":0.0,"r":["a","b","c","d","e"]}
    }


    #
    # tls=["a","b","c"]
    #
    # data={
    #
    #     "w2":{"g":100.0,"r":["a","b","c"]},
    #     "w3":{"g":100.0,"r":["a","b","c"]},
    #     "w4":{"g":100.0,"r":["a","b","c"]},
    #     "w5":{"g":100.0,"r":["a","b","c"]},
    #     "w7":{"g":100.0,"r":["a","b","c"]},
    #     "w9":{"g":900.0,"r":["a","b","c"]},
    #     "w10":{"g":900.0,"r":["a","b","c"]},
    #     "w11":{"g":900.0,"r":["a","b","c"]},
    #     "w13":{"g":900.0,"r":["a","b","c"]},
    #     "w14":{"g":900.0,"r":["a","b","c"]}
    # }

    wells=list(data.keys())


    population_num=50
    max_generations=100
    mutate_rate=0.05
    less_times=30

    population=make_population(population_num,len(tls))

    new_population=[]
    iters=0
    avg_prev_scores_abs=0
    less=0
    best=0.0
    avgs=[]
    bests=[]

    while iters<max_generations:

        tot_score=0.0
        scores_abs=[]
        cols=[]
        for dna in population:
            score,col=survive(wells,dna,data,tls)
            scores_abs.append(score)
            cols.append(col)
            tot_score+=score

        scores=list(np.array(scores_abs)/tot_score)

        new_population=[]
        for i in range(population_num):

            # crossover
            new_dna_idx1=np.random.choice(np.arange(population_num), p=scores)
            new_dna_idx2=np.random.choice(np.arange(population_num), p=scores)

            sl=int(np.random.randint(population_num))
            # sl=int(population_num/2)
            child=population[new_dna_idx1][:sl]+population[new_dna_idx2][sl:]

            # mutate 1 element in dna
            mutate=np.random.choice([0,1],p=[1-mutate_rate,mutate_rate])
            if mutate:
                rand_idx=np.random.randint(len(child))
                rand_tl=np.random.choice(tls)
                child[rand_idx]=rand_tl

            # new population for next generation
            new_population.append(child)

        if avg_prev_scores_abs>np.average(scores_abs):
            less+=1
            if less>less_times:
                # print("+++")
                break
            else:
                population=new_population
                avg_prev_scores_abs=np.average(scores_abs)
        else:
            less=0
            population=new_population
            avg_prev_scores_abs=np.average(scores_abs)


        if best<max(scores_abs):
            best=max(scores_abs)
            best_idx=scores_abs.index(best)
            best_dna=population[best_idx]
            best_col=cols[best_idx]
        print("generation:",iters,np.average(scores_abs))

        avgs.append(np.average(scores_abs))
        bests.append(best)

        iters+=1

    print("---")

    # print(bests)
    # print(best_col,best)
    plt.plot(avgs)
    plt.plot(bests)
    plt.show()
