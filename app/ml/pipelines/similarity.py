import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def calculate_cosine_similarity(vec1, vec2):
    return cosine_similarity([vec1], [vec2])[0][0]
