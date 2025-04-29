import torch
from sentence_transformers import SentenceTransformer, util

class LectureSlideMapper:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def map_lecture_text_to_slides(self, segment_texts: list, slide_texts: list):
        """
        세그먼트(분리된 강의 텍스트) 리스트와 슬라이드 텍스트 리스트를 받아서 매핑 결과 리턴
        """
        # 슬라이드 임베딩 생성
        slide_embeddings = self.model.encode(slide_texts, convert_to_tensor=True)

        mapping_results = []

        for idx, segment in enumerate(segment_texts):
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
