import torch
from sentence_transformers import SentenceTransformer, util
from nltk.tokenize import sent_tokenize

class LectureSlideMapper:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def preprocess_and_split_text(self, text, max_sentences=10):
        sentences = sent_tokenize(text.strip())
        merged_sentences = []
        for i in range(0, len(sentences), max_sentences):
            segment = ' '.join(sentences[i:i + max_sentences])
            merged_sentences.append(segment)
        return merged_sentences

    def map_lecture_text_to_slides(self, lecture_text: str, slide_texts: list):
        # 슬라이드 임베딩 생성
        slide_embeddings = self.model.encode(slide_texts, convert_to_tensor=True)

        # 강의 텍스트를 세그먼트로 분리
        segments = self.preprocess_and_split_text(lecture_text)

        mapping_results = []

        for idx, segment in enumerate(segments):
            segment_embedding = self.model.encode(segment, convert_to_tensor=True)
            cos_similarities = util.cos_sim(segment_embedding, slide_embeddings)
            best_match_idx = torch.argmax(cos_similarities).item()

            result = {
                "segment_index": idx,
                "matched_slide_index": best_match_idx,
                "similarity_score": round(cos_similarities[0][best_match_idx].item(), 4),
            }
            mapping_results.append(result)

        return mapping_results
