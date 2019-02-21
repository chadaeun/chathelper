import pandas as pd
import re

def split_series(series, pattern):
    rows = []
    sent_idx = 0

    for qa_idx, sent_list in series.apply(lambda x: re.split(pattern, x)).items():
        for sent in sent_list:
            if sent.strip():
                rows.append([qa_idx, sent_idx, sent])
                sent_idx += 1

    df = pd.DataFrame(rows, columns=['qa_idx', 'sent_idx', 'sent'])
    return df
