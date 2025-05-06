def word_frequencies(text):
    words = text.lower().split()
    freq = {}
    for word in words:
        if word in freq:
            freq[word] += 1
        else:
            freq[word] = 1
    return freq


def compare_word_frequencies(correct_freq, user_freq):
    differences = {}
    total_positive_difference = 0  # Initialize the total of positive differences

    for word in correct_freq:
        if word in user_freq:
            if correct_freq[word] != user_freq[word]:
                difference = user_freq[word] - correct_freq[word]
                if difference > 0:
                    differences[word] = difference
                    total_positive_difference += difference

    return differences, total_positive_difference
