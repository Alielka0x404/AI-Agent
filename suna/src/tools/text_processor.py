import logging
import re
import traceback
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

# Check if NLTK is available
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize, word_tokenize
    NLTK_AVAILABLE = True
    
    # Download required NLTK resources
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
        
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
        
except ImportError:
    NLTK_AVAILABLE = False

class TextProcessor:
    """Tools for text processing and analysis."""
    
    def __init__(self, config=None):
        """
        Initialize the text processor.
        
        Args:
            config (dict, optional): Configuration for text processing
        """
        self.config = config or {}
        self.language = self.config.get("language", "english")
        
        # Check if required packages are available
        if not NLTK_AVAILABLE:
            logger.warning("NLTK not available. Please install with: pip install nltk")
    
    def summarize_text(self, text: str, max_sentences: int = 5, min_length: int = 10) -> Dict[str, Any]:
        """
        Summarize text using extractive method.
        
        Args:
            text (str): The text to summarize
            max_sentences (int, optional): Maximum number of sentences in the summary
            min_length (int, optional): Minimum length of sentences to include
            
        Returns:
            Dict[str, Any]: The summarization result
        """
        if not NLTK_AVAILABLE:
            return {
                "success": False,
                "error": "NLTK not available. Please install with: pip install nltk"
            }
            
        try:
            # Clean and normalize text
            text = self._clean_text(text)
            
            # Tokenize into sentences
            sentences = sent_tokenize(text)
            
            if len(sentences) <= max_sentences:
                return {
                    "success": True,
                    "summary": text,
                    "original_length": len(text),
                    "summary_length": len(text),
                    "reduction_percentage": 0,
                    "sentence_count": len(sentences)
                }
            
            # Filter out very short sentences
            sentences = [s for s in sentences if len(s) >= min_length]
            
            # Get stopwords for the language
            try:
                stop_words = set(stopwords.words(self.language))
            except:
                stop_words = set()
            
            # Calculate word frequencies
            word_frequencies = {}
            for sentence in sentences:
                for word in word_tokenize(sentence.lower()):
                    if word not in stop_words and word.isalnum():
                        if word not in word_frequencies:
                            word_frequencies[word] = 1
                        else:
                            word_frequencies[word] += 1
            
            # Normalize frequencies
            if word_frequencies:
                max_frequency = max(word_frequencies.values())
                for word in word_frequencies:
                    word_frequencies[word] = word_frequencies[word] / max_frequency
            
            # Calculate sentence scores
            sentence_scores = {}
            for i, sentence in enumerate(sentences):
                for word in word_tokenize(sentence.lower()):
                    if word in word_frequencies:
                        if i not in sentence_scores:
                            sentence_scores[i] = word_frequencies[word]
                        else:
                            sentence_scores[i] += word_frequencies[word]
            
            # Get top sentences
            top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
            top_sentences = top_sentences[:min(max_sentences, len(top_sentences))]
            top_sentences = sorted(top_sentences, key=lambda x: x[0])  # Sort by position
            
            # Create summary
            summary = ' '.join([sentences[i] for i, _ in top_sentences])
            
            return {
                "success": True,
                "summary": summary,
                "original_length": len(text),
                "summary_length": len(summary),
                "reduction_percentage": round((1 - len(summary) / len(text)) * 100, 2) if len(text) > 0 else 0,
                "sentence_count": len(top_sentences),
                "original_sentence_count": len(sentences)
            }
            
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> Dict[str, Any]:
        """
        Extract keywords from text.
        
        Args:
            text (str): The text to analyze
            max_keywords (int, optional): Maximum number of keywords to extract
            
        Returns:
            Dict[str, Any]: The extracted keywords
        """
        if not NLTK_AVAILABLE:
            return {
                "success": False,
                "error": "NLTK not available. Please install with: pip install nltk"
            }
            
        try:
            # Clean and normalize text
            text = self._clean_text(text)
            
            # Get stopwords for the language
            try:
                stop_words = set(stopwords.words(self.language))
            except:
                stop_words = set()
            
            # Tokenize and filter words
            words = word_tokenize(text.lower())
            words = [word for word in words if word.isalnum() and word not in stop_words and len(word) > 2]
            
            # Calculate word frequencies
            word_frequencies = {}
            for word in words:
                if word in word_frequencies:
                    word_frequencies[word] += 1
                else:
                    word_frequencies[word] = 1
            
            # Sort by frequency
            sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
            
            # Get top keywords
            keywords = []
            for word, frequency in sorted_words[:max_keywords]:
                keywords.append({
                    "word": word,
                    "frequency": frequency,
                    "score": frequency / len(words) if len(words) > 0 else 0
                })
            
            return {
                "success": True,
                "keywords": keywords,
                "total_words": len(words),
                "unique_words": len(word_frequencies)
            }
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.
        
        Args:
            text (str): The text to analyze
            
        Returns:
            Dict[str, Any]: The sentiment analysis result
        """
        if not NLTK_AVAILABLE:
            return {
                "success": False,
                "error": "NLTK not available. Please install with: pip install nltk"
            }
            
        try:
            # This is a simple rule-based sentiment analysis
            # For production use, consider using a more sophisticated approach
            
            # Clean and normalize text
            text = self._clean_text(text)
            
            # Load positive and negative word lists
            positive_words = self._get_positive_words()
            negative_words = self._get_negative_words()
            
            # Tokenize text
            words = word_tokenize(text.lower())
            
            # Count positive and negative words
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            
            # Calculate sentiment score
            total_count = positive_count + negative_count
            if total_count > 0:
                sentiment_score = (positive_count - negative_count) / total_count
            else:
                sentiment_score = 0
            
            # Determine sentiment label
            if sentiment_score > 0.1:
                sentiment = "positive"
            elif sentiment_score < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                "success": True,
                "sentiment": sentiment,
                "score": sentiment_score,
                "positive_words": positive_count,
                "negative_words": negative_count,
                "total_words": len(words)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract named entities from text.
        
        Args:
            text (str): The text to analyze
            
        Returns:
            Dict[str, Any]: The extracted entities
        """
        if not NLTK_AVAILABLE:
            return {
                "success": False,
                "error": "NLTK not available. Please install with: pip install nltk"
            }
            
        try:
            # Check if we have the necessary NLTK resources
            try:
                nltk.data.find('tokenizers/punkt')
                nltk.data.find('taggers/averaged_perceptron_tagger')
                nltk.data.find('chunkers/maxent_ne_chunker')
                nltk.data.find('corpora/words')
            except LookupError:
                nltk.download('punkt', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                nltk.download('maxent_ne_chunker', quiet=True)
                nltk.download('words', quiet=True)
            
            # Clean and normalize text
            text = self._clean_text(text)
            
            # Tokenize and tag words
            tokens = word_tokenize(text)
            tagged = nltk.pos_tag(tokens)
            
            # Extract named entities
            entities = nltk.ne_chunk(tagged)
            
            # Process entities
            extracted_entities = {
                "PERSON": [],
                "ORGANIZATION": [],
                "LOCATION": [],
                "DATE": [],
                "TIME": [],
                "MONEY": [],
                "PERCENT": [],
                "FACILITY": [],
                "GPE": []  # Geo-Political Entity
            }
            
            # Extract entities from the tree
            for entity in entities:
                if hasattr(entity, 'label'):
                    entity_type = entity.label()
                    entity_text = ' '.join([word for word, tag in entity.leaves()])
                    
                    if entity_type in extracted_entities:
                        if entity_text not in extracted_entities[entity_type]:
                            extracted_entities[entity_type].append(entity_text)
            
            # Remove empty entity types
            extracted_entities = {k: v for k, v in extracted_entities.items() if v}
            
            return {
                "success": True,
                "entities": extracted_entities,
                "entity_count": sum(len(v) for v in extracted_entities.values())
            }
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s.,!?]', '', text)
        
        return text.strip()
    
    def _get_positive_words(self) -> List[str]:
        """Get a list of positive words."""
        # This is a small sample list - in production, use a comprehensive lexicon
        return [
            'good', 'great', 'excellent', 'positive', 'wonderful', 'fantastic',
            'amazing', 'love', 'happy', 'joy', 'beautiful', 'best', 'better',
            'awesome', 'nice', 'perfect', 'brilliant', 'outstanding', 'superb',
            'delightful', 'pleasant', 'impressive', 'remarkable', 'splendid',
            'terrific', 'tremendous', 'exceptional', 'favorable', 'marvelous',
            'admirable', 'commendable', 'satisfactory', 'satisfying', 'pleasing'
        ]
    
    def _get_negative_words(self) -> List[str]:
        """Get a list of negative words."""
        # This is a small sample list - in production, use a comprehensive lexicon
        return [
            'bad', 'terrible', 'awful', 'horrible', 'negative', 'poor', 'worst',
            'hate', 'sad', 'unhappy', 'angry', 'annoyed', 'disappointed', 'frustrating',
            'useless', 'worthless', 'inferior', 'mediocre', 'inadequate', 'unacceptable',
            'disgusting', 'offensive', 'appalling', 'atrocious', 'dreadful', 'lousy',
            'miserable', 'pathetic', 'unsatisfactory', 'displeasing', 'dismal', 'grim',
            'unfavorable', 'unpleasant', 'disagreeable', 'distressing', 'troubling'
        ]