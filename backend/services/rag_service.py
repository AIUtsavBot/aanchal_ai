"""
MatruRaksha AI - Hybrid RAG Service with Supabase pgvector
Implements: Metadata Filtering → BM25 + pgvector → RRF Fusion → Gemini

Uses Supabase pgvector for vector storage and rank_bm25 for keyword matching.
No ChromaDB required - everything stays in Supabase!
"""

import os
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Import BM25 for sparse retrieval
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("⚠️ rank_bm25 not available. Install with: pip install rank_bm25")

# Import Gemini for embeddings (uses existing API key)
GEMINI_EMBEDDINGS_AVAILABLE = False
gemini_client = None
try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_EMBEDDINGS_AVAILABLE = True
        logger.info("✅ Gemini embeddings available")
    else:
        logger.warning("⚠️ GEMINI_API_KEY not set for embeddings")
except ImportError:
    logger.warning("⚠️ google-genai not available for embeddings")

# Import Supabase
try:
    from supabase import Client
    from services.supabase_service import supabase as shared_supabase
    SUPABASE_AVAILABLE = True
except ImportError:
    shared_supabase = None
    SUPABASE_AVAILABLE = False
    logger.warning("⚠️ Supabase not available")


@dataclass
class RetrievedCase:
    """A retrieved maternal health case with scores"""
    case_id: int
    age: int
    systolic_bp: int
    diastolic_bp: int
    blood_sugar: float
    body_temp: float
    heart_rate: int
    risk_level: str
    similarity_score: float
    bm25_score: float
    combined_score: float
    
    def to_context_string(self) -> str:
        """Convert case to context string for LLM"""
        return (
            f"Case: {self.age}yr, BP={self.systolic_bp}/{self.diastolic_bp}, "
            f"BS={self.blood_sugar}, Temp={self.body_temp}°F, HR={self.heart_rate}, "
            f"Risk={self.risk_level} (score={self.combined_score:.2f})"
        )


class HybridRAGService:
    """
    Hybrid RAG service using Supabase pgvector, combining:
    1. Metadata filtering (SQL WHERE clauses)
    2. BM25 sparse retrieval (keyword matching)
    3. pgvector dense retrieval (semantic similarity)
    4. Reciprocal Rank Fusion (RRF) for combining results
    """
    
    def __init__(self, csv_path: Optional[str] = None):
        self.csv_path = csv_path or self._find_csv()
        self.df: Optional[pd.DataFrame] = None
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[str] = []
        self.supabase: Optional[Client] = None
        self._initialized = False
        self._embeddings_loaded = False

        # Use shared Supabase client
        if shared_supabase:
            self.supabase = shared_supabase
            logger.info("✅ Using shared Supabase client for RAG")
        else:
            logger.warning("⚠️ Supabase client not available")
        
    def _find_csv(self) -> str:
        """Find the maternal health CSV file"""
        possible_paths = [
            Path(__file__).parent.parent.parent / "Maternal Health Risk Data Set.csv",
            Path(__file__).parent.parent / "data" / "Maternal Health Risk Data Set.csv",
            Path(__file__).parent.parent / "Maternal Health Risk Data Set.csv",
            Path.cwd() / "Maternal Health Risk Data Set.csv",
            Path.cwd() / "backend" / "data" / "Maternal Health Risk Data Set.csv",
            Path.cwd().parent / "Maternal Health Risk Data Set.csv",
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        raise FileNotFoundError(
            "Could not find 'Maternal Health Risk Data Set.csv'. "
            "Please provide the path explicitly."
        )
    
    def initialize(self) -> bool:
        """Initialize the RAG service - load data, create embeddings, build indices"""
        if self._initialized:
            return True
            
        try:
            logger.info("🔄 Initializing Hybrid RAG Service (Supabase pgvector)...")
            
            # Step 1: Load CSV data
            self._load_csv_data()
            
            # Step 2: Create document representations for BM25
            self._create_documents()
            
            # Step 3: Build BM25 index (local, in-memory)
            if BM25_AVAILABLE:
                self._build_bm25_index()
            
            # Step 4: Check if embeddings exist in Supabase, if not, populate them
            if self.supabase and GEMINI_EMBEDDINGS_AVAILABLE:
                self._ensure_embeddings_in_supabase()
            
            self._initialized = True
            logger.info(f"✅ RAG Service initialized with {len(self.df)} maternal health cases")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG Service: {e}")
            return False
    
    def _load_csv_data(self):
        """Load and preprocess the maternal health CSV"""
        logger.info(f"📊 Loading CSV from: {self.csv_path}")
        self.df = pd.read_csv(self.csv_path)
        
        # Normalize column names
        self.df.columns = [col.strip() for col in self.df.columns]
        
        # Clean RiskLevel column
        if 'RiskLevel' in self.df.columns:
            self.df['RiskLevel'] = self.df['RiskLevel'].str.strip().str.lower()
        
        # Add an ID column for reference
        self.df['case_id'] = range(len(self.df))
        
        logger.info(f"✅ Loaded {len(self.df)} records")
    
    def _create_documents(self):
        """Create text documents from each row for BM25 and embedding"""
        self.documents = []
        
        for _, row in self.df.iterrows():
            doc = (
                f"maternal health case age {row['Age']} years "
                f"blood pressure {row['SystolicBP']} over {row['DiastolicBP']} mmHg "
                f"systolic {row['SystolicBP']} diastolic {row['DiastolicBP']} "
                f"blood sugar {row['BS']} mmol glucose "
                f"body temperature {row['BodyTemp']} fahrenheit "
                f"heart rate {row['HeartRate']} bpm pulse "
                f"risk level {row['RiskLevel']} "
                f"{'hypertension high blood pressure' if row['SystolicBP'] >= 140 else ''} "
                f"{'hyperglycemia high sugar' if row['BS'] > 11 else ''}"
            )
            self.documents.append(doc.lower())
        
        logger.info(f"✅ Created {len(self.documents)} document representations")
    
    def _build_bm25_index(self):
        """Build BM25 index for sparse retrieval (local, in-memory)"""
        tokenized_docs = [doc.split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_docs)
        logger.info("✅ BM25 index built (in-memory)")
    
    def _get_gemini_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text using Gemini API"""
        if not gemini_client:
            return []
        
        try:
            result = gemini_client.models.embed_content(
                model="models/text-embedding-004",
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            return []
    
    def _get_gemini_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts using Gemini API"""
        if not gemini_client:
            return []
        
        embeddings = []
        # Process in batches of 100 (Gemini limit)
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                result = gemini_client.models.embed_content(
                    model="models/text-embedding-004",
                    contents=batch
                )
                for emb in result.embeddings:
                    embeddings.append(emb.values)
            except Exception as e:
                logger.error(f"Gemini batch embedding error: {e}")
                # Add empty embeddings for failed batch
                embeddings.extend([[] for _ in batch])
        
        return embeddings
    
    def _ensure_embeddings_in_supabase(self):
        """Check if embeddings exist in Supabase, populate if not"""
        try:
            # Check if table has data
            result = self.supabase.table("maternal_health_embeddings").select("id").limit(1).execute()
            
            if result.data and len(result.data) > 0:
                logger.info("✅ Embeddings already exist in Supabase")
                self._embeddings_loaded = True
                return
            
            # No data - need to populate
            logger.info("📥 Populating embeddings in Supabase pgvector...")
            self._populate_supabase_embeddings()
            
        except Exception as e:
            if "does not exist" in str(e).lower():
                logger.warning(f"⚠️ Table maternal_health_embeddings not found. Run the migration first!")
                logger.warning("⚠️ SQL migration: infra/supabase/rag_migration.sql")
            else:
                logger.warning(f"⚠️ Could not check/populate embeddings: {e}")
    
    def _populate_supabase_embeddings(self):
        """Populate Supabase with embeddings from CSV data using Gemini"""
        if not GEMINI_EMBEDDINGS_AVAILABLE:
            logger.warning("⚠️ Cannot populate embeddings: Gemini not available")
            return
        
        logger.info("🔄 Generating embeddings with Gemini (models/text-embedding-004)...")
        embeddings = self._get_gemini_embeddings_batch(self.documents)
        
        # Batch insert
        batch_size = 50
        for i in range(0, len(self.df), batch_size):
            batch_data = []
            for j in range(i, min(i + batch_size, len(self.df))):
                row = self.df.iloc[j]
                batch_data.append({
                    "case_id": j,
                    "age": int(row['Age']),
                    "systolic_bp": int(row['SystolicBP']),
                    "diastolic_bp": int(row['DiastolicBP']),
                    "blood_sugar": float(row['BS']),
                    "body_temp": float(row['BodyTemp']),
                    "heart_rate": int(row['HeartRate']),
                    "risk_level": str(row['RiskLevel']),
                    "document_text": self.documents[j],
                    "embedding": embeddings[j].tolist()
                })
            
            try:
                self.supabase.table("maternal_health_embeddings").insert(batch_data).execute()
            except Exception as e:
                logger.error(f"Failed to insert batch {i}: {e}")
        
        logger.info(f"✅ Populated {len(self.df)} embeddings in Supabase")
        self._embeddings_loaded = True
    
    def _bm25_search(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        """BM25 sparse retrieval (local)"""
        if not self.bm25:
            return []
        
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(int(idx), float(scores[idx])) for idx in top_indices if scores[idx] > 0]
    
    def _pgvector_search(
        self,
        query: str,
        top_k: int = 20,
        age_range: Optional[Tuple[int, int]] = None,
        risk_level: Optional[str] = None,
        bp_range: Optional[Tuple[int, int]] = None
    ) -> List[Tuple[int, float]]:
        """pgvector dense retrieval via Supabase RPC using Gemini embeddings"""
        if not self.supabase or not GEMINI_EMBEDDINGS_AVAILABLE:
            return []
        
        try:
            # Generate query embedding with Gemini
            query_embedding = self._get_gemini_embedding(query.lower())
            if not query_embedding:
                return []
            
            # Call Supabase RPC function
            result = self.supabase.rpc("search_similar_maternal_cases", {
                "query_embedding": query_embedding,
                "age_min": age_range[0] if age_range else None,
                "age_max": age_range[1] if age_range else None,
                "risk_filter": risk_level.lower() if risk_level else None,
                "bp_min": bp_range[0] if bp_range else None,
                "bp_max": bp_range[1] if bp_range else None,
                "match_count": top_k
            }).execute()
            
            if result.data:
                return [(row['case_id'], row['similarity']) for row in result.data]
            
        except Exception as e:
            logger.warning(f"⚠️ pgvector search failed: {e}")
            # Fallback to local search if Supabase fails
            return self._local_vector_search(query, top_k, age_range)
        
        return []
    
    def _local_vector_search(
        self,
        query: str,
        top_k: int = 20,
        age_range: Optional[Tuple[int, int]] = None
    ) -> List[Tuple[int, float]]:
        """Fallback: local vector search when Supabase is unavailable"""
        if not GEMINI_EMBEDDINGS_AVAILABLE:
            return []
        
        query_embedding = self._get_gemini_embedding(query.lower())
        if not query_embedding:
            return []
        
        doc_embeddings = self._get_gemini_embeddings_batch(self.documents)
        if not doc_embeddings:
            return []
        
        query_embedding = np.array(query_embedding)
        doc_embeddings = np.array(doc_embeddings)
        
        # Cosine similarity
        similarities = np.dot(doc_embeddings, query_embedding) / (
            np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Apply age filter if provided
        if age_range:
            for i, row in self.df.iterrows():
                if not (age_range[0] <= row['Age'] <= age_range[1]):
                    similarities[i] = -1
        
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [(int(idx), float(similarities[idx])) for idx in top_indices if similarities[idx] > 0]
    
    def _reciprocal_rank_fusion(
        self,
        bm25_results: List[Tuple[int, float]],
        vector_results: List[Tuple[int, float]],
        k: int = 60
    ) -> List[Tuple[int, float, float, float]]:
        """Combine BM25 and vector results using RRF"""
        scores = {}
        
        for rank, (case_id, score) in enumerate(bm25_results):
            if case_id not in scores:
                scores[case_id] = {"bm25": 0, "vector": 0, "bm25_raw": 0, "vector_raw": 0}
            scores[case_id]["bm25"] = 1 / (k + rank + 1)
            scores[case_id]["bm25_raw"] = score
        
        for rank, (case_id, score) in enumerate(vector_results):
            if case_id not in scores:
                scores[case_id] = {"bm25": 0, "vector": 0, "bm25_raw": 0, "vector_raw": 0}
            scores[case_id]["vector"] = 1 / (k + rank + 1)
            scores[case_id]["vector_raw"] = score
        
        combined = [
            (case_id, s["bm25_raw"], s["vector_raw"], s["bm25"] + s["vector"])
            for case_id, s in scores.items()
        ]
        
        combined.sort(key=lambda x: x[3], reverse=True)
        return combined
    
    def retrieve_similar_cases(
        self,
        query: str,
        top_k: int = 3,
        age_range: Optional[Tuple[int, int]] = None,
        risk_level: Optional[str] = None,
        bp_range: Optional[Tuple[int, int]] = None
    ) -> List[RetrievedCase]:
        """
        Main retrieval method using hybrid approach:
        1. BM25 search (local)
        2. pgvector search (Supabase)
        3. RRF fusion
        """
        if not self._initialized:
            if not self.initialize():
                return []
        
        # BM25 search (local, always available)
        bm25_results = self._bm25_search(query, top_k=20)
        
        # Vector search (Supabase pgvector with metadata filtering)
        vector_results = self._pgvector_search(
            query, top_k=20, age_range=age_range, 
            risk_level=risk_level, bp_range=bp_range
        )
        
        # Combine with RRF
        fused_results = self._reciprocal_rank_fusion(bm25_results, vector_results)
        
        # Build RetrievedCase objects
        retrieved_cases = []
        for case_id, bm25_score, vector_score, combined_score in fused_results[:top_k]:
            if case_id < len(self.df):
                row = self.df.iloc[case_id]
                retrieved_cases.append(RetrievedCase(
                    case_id=int(case_id),
                    age=int(row['Age']),
                    systolic_bp=int(row['SystolicBP']),
                    diastolic_bp=int(row['DiastolicBP']),
                    blood_sugar=float(row['BS']),
                    body_temp=float(row['BodyTemp']),
                    heart_rate=int(row['HeartRate']),
                    risk_level=str(row['RiskLevel']),
                    similarity_score=vector_score,
                    bm25_score=bm25_score,
                    combined_score=combined_score
                ))
        
        logger.info(f"🔍 Retrieved {len(retrieved_cases)} similar cases (BM25: {len(bm25_results)}, Vector: {len(vector_results)})")
        return retrieved_cases
    
    def get_risk_context(
        self,
        age: int,
        systolic_bp: int,
        diastolic_bp: int,
        blood_sugar: float,
        heart_rate: Optional[int] = None,
        body_temp: Optional[float] = None
    ) -> str:
        """Get context string for risk assessment by finding similar cases."""
        query = f"maternal age {age} blood pressure {systolic_bp} {diastolic_bp} blood sugar {blood_sugar}"
        if heart_rate:
            query += f" heart rate {heart_rate}"
        if body_temp:
            query += f" temperature {body_temp}"
        
        age_range = (max(10, age - 5), min(70, age + 5))
        
        cases = self.retrieve_similar_cases(query=query, top_k=3, age_range=age_range)
        
        if not cases:
            return "No similar historical cases found."
        
        context_parts = ["Historical similar maternal health cases:"]
        for i, case in enumerate(cases, 1):
            context_parts.append(f"{i}. {case.to_context_string()}")
        
        risk_counts = {"high risk": 0, "mid risk": 0, "low risk": 0}
        for case in cases:
            risk_counts[case.risk_level] = risk_counts.get(case.risk_level, 0) + 1
        
        context_parts.append(f"\nRisk distribution in similar cases: {risk_counts}")
        return "\n".join(context_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized",
            "total_cases": len(self.df),
            "risk_distribution": self.df['RiskLevel'].value_counts().to_dict(),
            "age_range": (int(self.df['Age'].min()), int(self.df['Age'].max())),
            "bm25_available": BM25_AVAILABLE,
            "gemini_embeddings_available": GEMINI_EMBEDDINGS_AVAILABLE,
            "supabase_connected": self.supabase is not None,
            "embeddings_in_supabase": self._embeddings_loaded
        }
    
    def add_new_case(
        self,
        age: int,
        systolic_bp: int,
        diastolic_bp: int,
        blood_sugar: float,
        body_temp: float,
        heart_rate: int,
        risk_level: str,
        mother_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new maternal health case to the RAG database.
        This enables continuous learning - the database grows with real cases!
        
        Called when:
        - A new risk assessment is completed
        - A mother's health data is recorded
        - Outcomes are confirmed (for training data quality)
        
        Returns:
            dict with success status and case_id
        """
        if not self._initialized:
            self.initialize()
        
        # Normalize risk level
        risk_level = risk_level.strip().lower()
        if risk_level not in ['high risk', 'mid risk', 'low risk']:
            # Map common variations
            risk_map = {
                'high': 'high risk', 'moderate': 'mid risk', 'medium': 'mid risk',
                'low': 'low risk', 'critical': 'high risk'
            }
            risk_level = risk_map.get(risk_level, 'mid risk')
        
        # Generate next case_id
        try:
            result = self.supabase.table("maternal_health_embeddings")\
                .select("case_id")\
                .order("case_id", desc=True)\
                .limit(1)\
                .execute()
            next_case_id = (result.data[0]['case_id'] + 1) if result.data else len(self.df)
        except Exception:
            next_case_id = len(self.df) if self.df is not None else 1015
        
        # Create document text for BM25 and embedding
        doc_text = (
            f"maternal health case age {age} years "
            f"blood pressure {systolic_bp} over {diastolic_bp} mmHg "
            f"systolic {systolic_bp} diastolic {diastolic_bp} "
            f"blood sugar {blood_sugar} mmol glucose "
            f"body temperature {body_temp} fahrenheit "
            f"heart rate {heart_rate} bpm pulse "
            f"risk level {risk_level} "
            f"{'hypertension high blood pressure' if systolic_bp >= 140 else ''} "
            f"{'hyperglycemia high sugar' if blood_sugar > 11 else ''}"
        ).lower()
        
        # Generate embedding using Gemini
        embedding = self._get_gemini_embedding(doc_text)
        if not embedding:
            return {"success": False, "error": "Failed to generate embedding"}
        
        # Insert into Supabase pgvector
        try:
            insert_data = {
                "case_id": next_case_id,
                "age": age,
                "systolic_bp": systolic_bp,
                "diastolic_bp": diastolic_bp,
                "blood_sugar": float(blood_sugar),
                "body_temp": float(body_temp),
                "heart_rate": heart_rate,
                "risk_level": risk_level,
                "document_text": doc_text,
                "embedding": embedding
            }
            
            self.supabase.table("maternal_health_embeddings").insert(insert_data).execute()
            logger.info(f"✅ Added new case #{next_case_id} to RAG database (risk: {risk_level})")
            
        except Exception as e:
            logger.error(f"❌ Failed to insert new case: {e}")
            return {"success": False, "error": str(e)}
        
        # Update local dataframe for BM25
        if self.df is not None:
            new_row = pd.DataFrame([{
                'Age': age,
                'SystolicBP': systolic_bp,
                'DiastolicBP': diastolic_bp,
                'BS': blood_sugar,
                'BodyTemp': body_temp,
                'HeartRate': heart_rate,
                'RiskLevel': risk_level,
                'case_id': next_case_id
            }])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            self.documents.append(doc_text)
            
            # Rebuild BM25 index with new document
            if BM25_AVAILABLE:
                tokenized_docs = [doc.split() for doc in self.documents]
                self.bm25 = BM25Okapi(tokenized_docs)
                logger.info(f"🔄 Rebuilt BM25 index with {len(self.documents)} documents")
        
        return {
            "success": True,
            "case_id": next_case_id,
            "risk_level": risk_level,
            "total_cases": len(self.df) if self.df is not None else next_case_id + 1
        }


# Global instance
_rag_service: Optional[HybridRAGService] = None


def get_rag_service() -> HybridRAGService:
    """Get or create the global RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = HybridRAGService()
    return _rag_service


def retrieve_similar_cases(
    query: str,
    top_k: int = 5,
    age_range: Optional[Tuple[int, int]] = None,
    risk_level: Optional[str] = None
) -> List[RetrievedCase]:
    """Convenience function for retrieving similar cases"""
    return get_rag_service().retrieve_similar_cases(
        query=query, top_k=top_k, age_range=age_range, risk_level=risk_level
    )


def get_risk_context(
    age: int,
    systolic_bp: int,
    diastolic_bp: int,
    blood_sugar: float,
    heart_rate: Optional[int] = None,
    body_temp: Optional[float] = None
) -> str:
    """Convenience function for getting risk context"""
    return get_rag_service().get_risk_context(
        age=age, systolic_bp=systolic_bp, diastolic_bp=diastolic_bp,
        blood_sugar=blood_sugar, heart_rate=heart_rate, body_temp=body_temp
    )


def add_case_to_rag(
    age: int,
    systolic_bp: int,
    diastolic_bp: int,
    blood_sugar: float,
    body_temp: float,
    heart_rate: int,
    risk_level: str,
    mother_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to add a new case to RAG database.
    Call this after each risk assessment to enable continuous learning!
    
    Example:
        result = add_case_to_rag(
            age=28, systolic_bp=140, diastolic_bp=90,
            blood_sugar=15.0, body_temp=98.6, heart_rate=82,
            risk_level="high risk"
        )
        print(f"Added case #{result['case_id']}, total: {result['total_cases']}")
    """
    return get_rag_service().add_new_case(
        age=age, systolic_bp=systolic_bp, diastolic_bp=diastolic_bp,
        blood_sugar=blood_sugar, body_temp=body_temp, heart_rate=heart_rate,
        risk_level=risk_level, mother_id=mother_id
    )

