def answershort(question, answer_list, user_answer):
    print("QUESTION::", question)
    
    # Initialize content score
    content_score = 0.0
    
    # Convert user_answer to lowercase
    user_answer = user_answer.lower()

    user_answer_unsplit = user_answer

    user_answer = user_answer.split()
    
    # Convert all answers in answer_list to lowercase
    answer_list = [answer.lower() for answer in answer_list]
    
    for words in user_answer:
        # Check if user_answer is in the list of possible answers
        if words in answer_list:
            # Assign a score of 1.0 if the answer is correct
            content_score = 1.0

    print("User Answer Unsplit::", user_answer_unsplit)

    if user_answer_unsplit in answer_list:
        content_score = 1.0
    
    return content_score
