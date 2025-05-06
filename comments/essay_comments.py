
def set_essay_comments(content_score , grammar_score , vocab_range_score ,spelling_score , form_score , general_linguistic_range_score , development_structure_coherence_score):
    sample_comments={}


   # Content score comment
    if content_score==3.0:
       sample_comments['content_score']='Well Done!'

    elif content_score>=2.0:
        sample_comments['content_score']='Try using more relevant content.'

    elif content_score>=1.0:
        sample_comments['content_score']='Try using more relevant content.'
    else:
        sample_comments['content_score']=' Your response contains irrelevant content. If this criterion is not met, you won’t get a score in rest of the enabling skills.'
        return sample_comments
    
    
   

    # Form Score comment
   
    if form_score==2.0:
        sample_comments['form_score']='Well Done!'
    elif form_score>=1.0:
        sample_comments['form_score']='Your response has to be within the word limit of 200 - 300 words only.'
    else:
        sample_comments['form_score'] = 'Your response has to be within the word limit of 200 - 300 words only.' #assumed by me
        return sample_comments





    # Grammer Comments Remaining 
    if grammar_score==2.0:
        sample_comments['grammar_score']='Well Done!'

    elif  grammar_score>=1.5 :
       sample_comments['grammar_score']='You can still improve your grammar. Hover on the marked grammatical errors to check the details.'
    elif grammar_score>=1.0:
        sample_comments['grammar_score']='You can still improve your grammar. Hover on the marked grammatical errors to check the details.'
    else:
        sample_comments['grammar_score']='Poor.You can still improve your grammar. Hover on the marked grammatical errors to check the details.' #Assumed by me

    # Vocabb Range Comment
    if vocab_range_score==2.0:
        sample_comments['vocab_Score']='Well Done!'
    else:
        sample_comments['vocab_Score']='Try using high vocabulary words to improve this score.'
    
    # Spelling Score Comment

    if spelling_score>=2.0:
        sample_comments['spelling_score']='Well Done!'
    elif spelling_score>=1:
        sample_comments['spelling_score']='You need to improve your spelling. Hover on the marked spelling errors to check the details.' 
    else:
        sample_comments['spelling_score']='Poor.You need to improve your spelling. Hover on the marked spelling errors to check the details.'  #assumed by me

    
    # Developement Structure Comment
    if development_structure_coherence_score>=2.0:
        sample_comments['development_structure_coherence_score']='Well Done!'
    elif development_structure_coherence_score>=1.0:
        sample_comments['development_structure_coherence_score']='Your essay needs to be organized & structured in a better way.'
    else:
        sample_comments['development_structure_coherence_score']='Poor. Your essay needs to be organized & structured in a better way.'
    

    
    
    # General Linguistic comment
    
    if general_linguistic_range_score>=2.0:
       sample_comments['general_linguistic_range_score']='Well Done!'
    elif general_linguistic_range_score>=1.0:
        sample_comments['general_linguistic_range_score']='Try to use more complex sentence structures & higher vocabulary.'
    else:
        sample_comments['general_linguistic_range_score']='Poor.Try to use more complex sentence structures & higher vocabulary.'  #assumed by me
   
    return sample_comments

    