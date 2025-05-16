import torch
import torch.nn.functional as F
import kss

from sentence_transformers import SentenceTransformer, util
from nltk.tokenize import sent_tokenize
from transformers import AutoTokenizer, AutoModel

class LectureSlideMapper:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def preprocess_and_split_text(self, text, max_sentences=10):
        """
        세그먼트 분리 (고정된 개수의 문장으로)
        """
        sentences = sent_tokenize(text.strip())
        merged_sentences = []
        for i in range(0, len(sentences), max_sentences):
            segment = ' '.join(sentences[i:i + max_sentences])
            merged_sentences.append(segment)
        return merged_sentences

    def map_lecture_text_to_slides(self, segment_texts: list, slide_texts: list):
        """
        세그먼트(분리된 강의 텍스트) 리스트와 슬라이드 텍스트 리스트를 받아서 매핑 결과 리턴
        """
        # 슬라이드 임베딩 생성
        slide_embeddings = self.model.encode(slide_texts, convert_to_tensor=True)

        mapping_results = []

        # 슬라이드 임베딩과 세그먼트 임베딩 값의 코싸인 유사도 비교 통한 매핑
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



class LectureSlideMapperKor:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("jhgan/ko-sroberta-multitask")
        self.model = AutoModel.from_pretrained("jhgan/ko-sroberta-multitask")

    def encode(self, text):
        """
        한 문장을 Ko-SRoBERTa 임베딩으로 변환 ([CLS] 벡터 사용)
        """
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state[:, 0, :]  # [CLS] 토큰 벡터

    def preprocess_and_split_text_kor(self, text, max_sentences=10):
        """
        세그먼트 분리: kss로 문장 분리한 뒤, max_sentences 단위로 묶음
        """
        sentences = kss.split_sentences(text.strip())
        merged_sentences = []
        for i in range(0, len(sentences), max_sentences):
            segment = ' '.join(sentences[i:i + max_sentences])
            merged_sentences.append(segment)
        return merged_sentences

    def map_lecture_text_to_slides_kor(self, segment_texts: list, slide_texts: list):
        # 슬라이드 임베딩 생성
        slide_embeddings = torch.cat([self.encode(text) for text in slide_texts], dim=0)
        mapping_results = []

        for idx, segment in enumerate(segment_texts):
            segment_embedding = self.encode(segment)  # shape: (1, hidden_size)
            # 코사인 유사도 계산 (normalize 먼저)
            sim_scores = F.cosine_similarity(segment_embedding, slide_embeddings)
            best_match_idx = torch.argmax(sim_scores).item()

            result = {
                "segment_index": idx,
                "matched_slide_index": best_match_idx,
                "similarity_score": round(sim_scores[best_match_idx].item(), 4),
            }
            mapping_results.append(result)

        return mapping_results
