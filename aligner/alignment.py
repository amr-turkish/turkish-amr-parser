from util.alignment_utils import load_gazetteer_from_json, load_gazetteer_from_txt



### Predefined Conversions

dep2amr = {"POSSESSOR":"poss"}

subjects= {"A1sg":"ben","A2sg":"sen","A3sg":"O","A1pl":"biz","A2pl":"siz","A3pl":"onlar"}
pronouns = {"P1sg":"ben","P2sg":"sen","P3sg":"O","P1pl":"biz","P2pl":"siz","P3pl":"onlar"}

amrtag2rel={"AM-MNR":"manner","A-A":"A0","AM-LOC":"location","AM-TMP":"time","MODIFIER":"mod","AM-INS":"instrument",
           "POSSESSOR":"poss","AM-DIR":"direction","AM-EXT":"frequeny",
           "AM-COM":"accompanier","C-A1":"A1","A-A-of":"A0-of","AM-TMP-of":"be-temporally-at-91","MWE:TIMEX:DATE":"time",
           "AM-GOL-of":"have-goal-91","MWE:FORMEX":"mod","AM-LOC-of":"be-located-at-91","AM-EXT-of":"have-frequency-91"}

special_relations = {"OBJECT":"A1","SUBJECT":"A0"}

rel2removed=["AM-LVB","INTENSIFIER","DETERMINER","PUNCTUATION","AM-ADV","AM-DIS","MWE:COMP","RELATIVIZER","APPOSITION"]
key2removed=["dek","diye","asla","eğer","çünkü","üzere","ile","başka"]
time_temporal_words={"önce":"önce","sonra":"sonra","beri":"önce","boyunca":"şimdi"}
number_relations = ["MWE:TIMEX:DATE","MWE:NUMEX","MODIFIER","MWE:NUMEX:MONEY","DETERMINER"]



### Gazetteer Based Conversions
countries = load_gazetteer_from_json('aligner/gazetteers','countries.json')
cities = load_gazetteer_from_json('aligner/gazetteers','cities.json')
questions = load_gazetteer_from_json('aligner/gazetteers','questions.json')
medium = load_gazetteer_from_txt('aligner/gazetteers','medium.txt')
directions = load_gazetteer_from_txt('aligner/gazetteers','directions.txt')
aproximation = load_gazetteer_from_json('aligner/gazetteers','approximation.json')
quantities = load_gazetteer_from_json('aligner/gazetteers','quantites.json')
nationalities = load_gazetteer_from_json('aligner/gazetteers','nationalities.json')
date_entities = load_gazetteer_from_json('aligner/gazetteers','date-entities.json')



locations = {}
locations.update(countries)
locations.update(cities)



key2amr={"remove-token-pre-token-up":{"bile":"concession","rağmen":"concession",
                                      "karşın":"concession","birlikte":"accompanier"},
         "up-token-parent-down":{"rusça":"medium","ingilizce":"medium","almanca":"medium","rumca":"medium",
                                 "daima":"extents","sonsuz":"extents","ebediyen":"extents"},
         "function-based":{"ilgili":"add_topic","böyle":"add_benze_frame","şöyle":"add_benze_frame",
                           "belki":"handle_modality_words","olarak":"change_olarak"},
         "only-parent-rel":{"çok":"degree","biraz":"degree","tabii":"mod","tabi":"mod"},
         "special_cases":["kişi","gibi","şey"],
         "negation":["değil"],
         "have-degree":{"en":"have-degree-91","daha":"have-degree-91","kadar":"have-degree-91"},
         "have-relation":["eş","koca"],
         "det-to-mod":["bu","bazı","bir"],
         "non-relations":["için"],
         "percentage":["yüzde","binde"],
         # "question":["mı","mi","mu","mü"],
         "question":questions['question'],
         # "wh-questions":{"nasıl":"manner","nere":"location","ne":"A1","neden":"cause"},
         "wh-questions":questions['wh-questions'],
         "locations":locations,
         "nationality" : nationalities,
         "date-entity" : date_entities }

         # "locations":{"istanbul":"şehir","diyarbakır":"şehir","ırak":"ülke","israil":"ülke","roma":"şehir",
         #              "türkiye":"ülke","kocaeli":"şehir"},
    #     "date-entity":{"çarşamba":"weekday","kasım":"month","aralık":"month","ocak":"month"},
       #  "nationality":{"fransız":"fransa","rus":"rusya","türk":"türkiye","avrupalı":"avrupa","bulgar":"bulgaristan"},






# quantities={"yıl":"temporal-quantity","ay":"temporal-quantity","gün":"temporal-quantity","hafta":"temporal-quantity",
#             "saat":"temporal-quantity","dakika":"temporal-quantity","saniye":"temporal-quantity",
#             "akşam":"temporal-quantity","sabah":"temporal-quantity",
#            "kilometre":"distant-quantity","metre":"distant-quantity","mil":"distant-quantity",
#             "santimetre":"distant-quantity","milimetre":"distant-quantity",
#             "tl":"monetary-quantity","lira":"monetary-quantity",
#             "dolar":"monetary-quantity","sent":"monetary-quantity","euro":"monetary-quantity","kuruş":"monetary-quantity"}
#
# aproximation={"onlarca":"several","yüzlerce":"several","binlerce":"several","onbinlerce":"several",
#               "yüzbinlerce":"several","milyonlarca":"several","yüzden":"several","binden":"several",
#              "yıllar":"more-than","aylar":"more-than","günler":"more-than","haftalar":"more-than","yıllarda":"more-than",
#              "yıllarca":"more-than","aylarca":"more-than","günlerce":"more-than","haftalarca":"more-than"}
#
