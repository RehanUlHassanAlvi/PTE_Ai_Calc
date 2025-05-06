
def set_summarizespoken_comments(content_score ,form_score , grammar_score , vocab_range_score, pte_type, spelling_score ):
    sample_comments={}

   # Content score comment
    if content_score == 2.0:
       sample_comments['Content']='Well Done!'
    elif content_score >= 1.0:
        sample_comments['Content']= 'You need to add more content from the passage.'
    else:
        sample_comments['Content']=' Your response contains irrelevant content. If this criterion is not met, you won’t get a score in rest of the enabling skills.'
    
    if spelling_score >= 2.0:
        sample_comments['spelling_score']='Well Done!'
    elif spelling_score >= 1.0:
        sample_comments['spelling_score']='You need to improve your spelling. Hover on the marked spelling errors to check the details.' 
    else:
        sample_comments['spelling_score']='Poor.You need to improve your spelling. Hover on the marked spelling errors to check the details.'  #assumed by me


    # Form Score comment

    if pte_type == "pte core":
        if form_score == 2.0:
            sample_comments['Form']='Well Done!'
        elif form_score >= 1.0:
            sample_comments['Form']= 'Your response has to be within the word limit of 20 - 30 words.'
        else:
            sample_comments['Form'] = 'Your response has to be within the word limit of 20 - 30 words only. If this criterion is not met, you won’t get a score in rest of the enabling skills.'

    elif pte_type == "pte academic":
        if form_score == 2.0:
            sample_comments['Form']='Well Done!'
        elif form_score >= 1.0:
            sample_comments['Form']= 'Your response has to be within the word limit of 50 - 70 words.'
        else:
            sample_comments['Form'] = 'Your response has to be within the word limit of 50 - 70 words only. If this criterion is not met, you won’t get a score in rest of the enabling skills.'




    # Grammer Comments 
    if grammar_score == 2.0:
        sample_comments['Grammar']='Well Done!'
    elif grammar_score >= 1.0:
        sample_comments['Grammar']='You can still improve your grammar. Hover on the marked grammatical errors to check the details.'
    else:
        sample_comments['Grammar']='Poor.You can still improve your grammar. Hover on the marked grammatical errors to check the details.' #Assumed by me



    # Vocab Range Comment
    if vocab_range_score == 2.0:
        sample_comments['Vocabulary']='Well Done!'
    elif vocab_range_score >= 1.0:
        sample_comments['Vocabulary']='Try using words from the passage.'
    else:
        sample_comments['Vocabulary']='Poor. Try using words from the passage.'
    
    return sample_comments

