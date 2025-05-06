import spacy
from spacy.tokens import Doc
import re

def count_multiple_spaces(text):
    print("in count spaces")
    pattern = r'\b(\w+)\s{2,}(\w+)\b'
    matches = re.finditer(pattern, text)
    print("matches:", matches)
    multispace_indices = []    
    results = []
    for match in matches:
        start_index = match.start()
        end_index = match.end()
        matched_text = match.group()
        results.append(matched_text)
        multispace_indices.append((start_index, end_index))
    return len(results), results, multispace_indices

def merge_appos_words(doc):
  doc_list = list(doc)
  print(type(doc))

  nlp = spacy.load('en_core_web_sm')

  remove_index=[]
  i=0
  check=0
  for token in doc_list:

    if i<len(doc_list)-1:
      next_token = doc_list[i + 1]

      if next_token.text.startswith("'"):
        check=1
        merged_str=token.text + next_token.text
        merged_str = nlp(merged_str)

        doc_list[i]= merged_str
        remove_index.append(i+1)
      else:
        pass
    i+=1



  if check==1:
    # print("doc list before remove: ",doc_list )
    doc_list = [token for i, token in enumerate(doc_list) if i not in remove_index]
    # print("doc list after remove: ",doc_list )
    modified_doc = Doc(nlp.vocab, words=[token.text for token in doc_list])

    # print("modified_doc: ", modified_doc)

    return modified_doc
  else:
    # print("no apostrophe case: ", doc)
    return doc
