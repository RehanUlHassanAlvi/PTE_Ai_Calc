
def set_summary_comments(content_score ,form_score , grammar_score , vocab_range_score, pte_type ):
    sample_comments={}

   # Content score comment
    if content_score==2.0:
       sample_comments['Content']='Well Done!'
    elif content_score>=1.0:
        sample_comments['Content']= 'You need to add more content from the passage.'
    else:
        sample_comments['Content']=' Your response contains irrelevant content. If this criterion is not met, you won’t get a score in rest of the enabling skills.'
    


    # Form Score comment

    if pte_type == "pte core":
        if form_score==2.0:
            sample_comments['Form']='Well Done!'
        elif form_score>=1.0:
            sample_comments['Form']= 'Your response has to be within the word limit of 5 - 60 words only.'
        else:
            sample_comments['Form'] = 'Your response has to be within the word limit of 5 - 60 words only. If this criterion is not met, you won’t get a score in rest of the enabling skills.'

    elif pte_type == "pte academic":
        if form_score==1.0:
            sample_comments['Form']='Well Done!'
        elif form_score>=0.0:
            sample_comments['Form']= 'Your response has to be within the word limit of 5 - 75 words only.'




    # Grammer Comments 
    if grammar_score==2.0:
        sample_comments['Grammar']='Well Done!'
    elif grammar_score>=1.0:
        sample_comments['Grammar']='You can still improve your grammar. Hover on the marked grammatical errors to check the details.'
    else:
        sample_comments['Grammar']='Poor.You can still improve your grammar. Hover on the marked grammatical errors to check the details.' #Assumed by me



    # Vocab Range Comment
    if vocab_range_score==2.0:
        sample_comments['Vocabulary']='Well Done!'
    elif vocab_range_score>=1.0:
        sample_comments['Vocabulary']='Try using words from the passage with correct spellings.'
    else:
        sample_comments['Vocabulary']='Poor. Try using words from the passage with correct spellings.'
    
    return sample_comments

