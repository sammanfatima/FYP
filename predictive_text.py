# predictive_text.py → 100% WHATSAPP JESA PREDICTION + NO BAKWAS + USER MEMORY FOREVER
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import re
import os
import json
from collections import Counter
import threading

class EyeTypingPredictor:
    def __init__(self):
        print("Loading Real WhatsApp-Level Predictor... (15-25 sec first time)")
        
        self.model_name = "distilgpt2"
        self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
        self.model = GPT2LMHeadModel.from_pretrained(self.model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model.eval()

        if torch.cuda.is_available():
            self.model.to('cuda')
            print("GPU Active → Super Fast!")

        # User history file — ab restart par bhi yaad rahega!
        self.history_file = "user_words.json"
        self.user_words = self.load_user_words()

        # Real WhatsApp-style common words (sabse zyada use hone wale)
        self.common_words = [
            "i", "you", "the", "to", "a", "me", "and", "is", "in", "my",
            "it", "for", "of", "on", "are", "that", "with", "have", "was", "at",
            "good", "love", "happy", "very", "so", "just", "like", "know", "but", "be",
            "morning", "night", "thanks", "please", "sorry", "yes", "no", "ok", "okay",
            "haha", "lol", "really", "today", "home", "work", "time", "how", "what", "why",
            "going", "get", "see", "come", "can", "do", "want", "your", "not", "this"
        ]

        print("WhatsApp Predictor Ready — Ab bilkul asli jaisa lagega!")

    def load_user_words(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"User history loaded: {len(data)} words remembered!")
                    return Counter(data)
            except:
                return Counter()
        return Counter()

    def save_user_words(self):
        def save():
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.user_words), f, ensure_ascii=False)
        threading.Thread(target=save, daemon=True).start()

    def suggest_next_words(self, prefix="", num_suggestions=3):
        if not prefix.strip():
            return ["I", "you", "the"]

        # Clean prefix
        prefix = prefix.strip()
        words = prefix.split()
        current_word = words[-1].lower() if words else ""

        # 1. USER KA APNA STYLE (jo wo sabse zyada type karta hai)
        personal_matches = []
        for word, count in self.user_words.most_common(30):
            if word.startswith(current_word) and word != current_word:
                personal_matches.append(word.capitalize() if prefix.endswith(" ") else word)
                if len(personal_matches) >= num_suggestions:
                    return personal_matches

        if personal_matches:
            return personal_matches

        # 2. COMMON WHATSAPP WORDS (bilkul real!)
        common_matches = []
        for word in self.common_words:
            if word.startswith(current_word) and word != current_word:
                common_matches.append(word.capitalize() if prefix.endswith(" ") else word)
                if len(common_matches) >= num_suggestions:
                    # User ko yaad karwao
                    self.user_words[current_word] += 1
                    self.save_user_words()
                    return common_matches

        if common_matches:
            self.user_words[current_word] += 1
            self.save_user_words()
            return common_matches

        # 3. AI SMART PREDICTION (sirf jab kuch na mile)
        try:
            input_text = prefix[-50:]  # Last 50 chars
            inputs = self.tokenizer(input_text + " ", return_tensors="pt", truncation=True, max_length=64)
            if torch.cuda.is_available():
                inputs = inputs.to('cuda')

            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=5,
                    num_return_sequences=4,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=30,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    no_repeat_ngram_size=2
                )

            suggestions = []
            for output in outputs:
                text = self.tokenizer.decode(output[len(inputs[0]):], skip_special_tokens=True).strip()
                next_word = text.split()[0] if text.split() else ""
                next_word = re.sub(r'[^\w]', '', next_word).lower()

                if (next_word and 
                    len(next_word) > 1 and 
                    next_word != current_word and 
                    next_word not in [s.lower() for s in suggestions]):
                    
                    display_word = next_word.capitalize() if prefix.endswith(" ") else next_word
                    suggestions.append(display_word)

            if suggestions:
                self.user_words[current_word] += 1
                self.save_user_words()
                return suggestions[:num_suggestions]

        except:
            pass

        # Final safe suggestions
        safe = ["you", "the", "I", "to", "a", "and"]
        result = []
        for w in safe:
            if w.startswith(current_word):
                result.append(w.capitalize() if prefix.endswith(" ") else w)
        return result[:num_suggestions] or ["you", "I", "the"][:num_suggestions]