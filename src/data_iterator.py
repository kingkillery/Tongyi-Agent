"""
Data Iterator for Tongyi DeepResearch
Enables high-quality data generation through iterative refinement cycles.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterator, Callable

from cas_store import CAS
from verifier_gate import VerifierGate

logger = logging.getLogger(__name__)


@dataclass
class DataItem:
    """Single data item with metadata and quality metrics."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    verification_status: str = "pending"  # pending, verified, failed
    sources: List[str] = field(default_factory=list)
    iteration: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass 
class IterationConfig:
    """Configuration for data iteration process."""
    max_iterations: int = 5
    quality_threshold: float = 0.8
    batch_size: int = 10
    verification_enabled: bool = True
    compression_ratio: float = 0.3
    cache_results: bool = True
    seed: int = 1337


class DataIterator:
    """Iterates through datasets to generate high-quality data using Tongyi DeepResearch."""
    
    def __init__(
        self,
        root: str = ".",
        config: Optional[IterationConfig] = None,
        cas_store: Optional[CAS] = None,
        verifier: Optional[VerifierGate] = None
    ):
        self.root = Path(root).absolute()
        self.config = config or IterationConfig()
        self.cas = cas_store or CAS()
        self.verifier = verifier or VerifierGate()
        self.iteration_history: List[Dict[str, Any]] = []
        
    def iterate_dataset(
        self,
        dataset_path: str,
        transform_fn: Callable[[DataItem], DataItem],
        quality_fn: Callable[[DataItem], float]
    ) -> Iterator[DataItem]:
        """
        Iterate through a dataset, applying transformations and quality improvements.
        
        Args:
            dataset_path: Path to input dataset (JSONL, CSV, etc.)
            transform_fn: Function to transform/analyze data items
            quality_fn: Function to score data quality
            
        Yields:
            DataItem: Improved data items
        """
        dataset_file = self.root / dataset_path
        if not dataset_file.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
            
        logger.info(f"Starting data iteration for {dataset_path}")
        
        # Load initial dataset
        raw_items = self._load_dataset(dataset_file)
        logger.info(f"Loaded {len(raw_items)} items from dataset")
        
        # Process in batches
        for batch_start in range(0, len(raw_items), self.config.batch_size):
            batch = raw_items[batch_start:batch_start + self.config.batch_size]
            yield from self._process_batch(batch, transform_fn, quality_fn)
    
    def _load_dataset(self, file_path: Path) -> List[DataItem]:
        """Load dataset from various formats."""
        suffix = file_path.suffix.lower()
        
        if suffix == ".jsonl":
            return self._load_jsonl(file_path)
        elif suffix == ".json":
            return self._load_json(file_path)
        elif suffix == ".csv":
            return self._load_csv(file_path)
        else:
            raise ValueError(f"Unsupported format: {suffix}")
    
    def _load_jsonl(self, file_path: Path) -> List[DataItem]:
        """Load JSONL dataset."""
        items = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    item = DataItem(
                        content=data.get('content', str(data)),
                        metadata=data.get('metadata', {}),
                        sources=data.get('sources', [])
                    )
                    items.append(item)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON at line {line_num}: {e}")
        return items
    
    def _load_json(self, file_path: Path) -> List[DataItem]:
        """Load JSON dataset."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return [
                DataItem(
                    content=item.get('content', str(item)),
                    metadata=item.get('metadata', {}),
                    sources=item.get('sources', [])
                )
                for item in data
            ]
        else:
            return [DataItem(
                content=data.get('content', str(data)),
                metadata=data.get('metadata', {}),
                sources=data.get('sources', [])
            )]
    
    def _load_csv(self, file_path: Path) -> List[DataItem]:
        """Load CSV dataset."""
        import csv
        
        items = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                # Combine all columns into content
                content = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
                item = DataItem(
                    content=content,
                    metadata={"row": row_num, "columns": list(row.keys())}
                )
                items.append(item)
        return items
    
    def _process_batch(
        self,
        batch: List[DataItem],
        transform_fn: Callable[[DataItem], DataItem],
        quality_fn: Callable[[DataItem], float]
    ) -> Iterator[DataItem]:
        """Process a batch of data items through iteration cycles."""
        
        current_batch = batch
        
        for iteration in range(self.config.max_iterations):
            logger.info(f"Processing iteration {iteration + 1}/{self.config.max_iterations}")
            iteration_start = time.time()
            
            improved_batch = []
            for item in current_batch:
                try:
                    # Apply transformation
                    improved_item = transform_fn(item)
                    improved_item.iteration = iteration + 1
                    
                    # Score quality
                    quality_score = quality_fn(improved_item)
                    improved_item.quality_score = quality_score
                    
                    # Verify if enabled
                    if self.config.verification_enabled:
                        verification_result = self._verify_item(improved_item)
                        improved_item.verification_status = verification_result
                    
                    # Cache if enabled
                    if self.config.cache_results:
                        self._cache_item(improved_item)
                    
                    improved_batch.append(improved_item)
                    
                    # Yield if meets quality threshold
                    if quality_score >= self.config.quality_threshold:
                        yield improved_item
                        
                except Exception as e:
                    logger.error(f"Error processing item: {e}")
                    # Yield original item as fallback
                    yield item
            
            # Update batch for next iteration
            current_batch = improved_batch
            
            iteration_time = time.time() - iteration_start
            avg_quality = (
                sum(item.quality_score for item in current_batch) / len(current_batch)
                if current_batch
                else 0.0
            )
            
            self.iteration_history.append({
                "iteration": iteration + 1,
                "duration_ms": iteration_time * 1000,
                "avg_quality": avg_quality,
                "batch_size": len(current_batch),
                "verified_count": sum(1 for item in current_batch if item.verification_status == "verified"),
            })
            
            logger.info(f"Iteration {iteration + 1} completed in {iteration_time:.2f}s, avg quality: {avg_quality:.3f}")
    
    def _verify_item(self, item: DataItem) -> str:
        """Verify a data item using the verifier gate."""
        try:
            # Extract claims from content (simplified)
            claims = [item.content]  # In practice, would extract individual claims
            
            # Verify against sources
            if item.sources:
                claim = self.verifier.verify_claim(item.content, item.sources)
                return "verified" if claim.verified else "failed"
            else:
                return "pending"  # No sources to verify against
                
        except Exception as e:
            logger.warning(f"Verification failed: {e}")
            return "failed"
    
    def _cache_item(self, item: DataItem) -> None:
        """Cache an item in CAS."""
        try:
            item_data = {
                "content": item.content,
                "metadata": item.metadata,
                "quality_score": item.quality_score,
                "iteration": item.iteration,
            }
            cas_key = self.cas.put(
                json.dumps(item_data).encode("utf-8"),
                url=None,
                fetched_at=None,
                content_type="application/json",
                parser_ver="data-iterator-1",
                outlinks=None,
            )
            # Store CAS key in metadata
            item.metadata["cas_key"] = cas_key
        except Exception as e:
            logger.warning(f"CAS caching failed: {e}")
    
    def get_iteration_stats(self) -> Dict[str, Any]:
        """Get statistics about the iteration process."""
        if not self.iteration_history:
            return {"message": "No iterations completed"}
            
        total_items = sum(h["batch_size"] for h in self.iteration_history)
        total_verified = sum(h["verified_count"] for h in self.iteration_history)
        avg_quality = (
            sum(h["avg_quality"] for h in self.iteration_history) / len(self.iteration_history)
            if self.iteration_history
            else 0.0
        )
        
        return {
            "total_iterations": len(self.iteration_history),
            "total_items_processed": total_items,
            "total_verified_items": total_verified,
            "verification_rate": total_verified / total_items if total_items > 0 else 0.0,
            "final_avg_quality": avg_quality,
            "iteration_history": self.iteration_history
        }


# Example transformation and quality functions
def example_transform_fn(item: DataItem) -> DataItem:
    """Example transformation function - cleans and structures content."""
    import re
    
    # Basic cleaning
    content = item.content.strip()
    content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
    content = re.sub(r'[^\w\s\.\,\!\?\-\(\)]', '', content)  # Remove special chars
    
    # Update metadata
    new_metadata = item.metadata.copy()
    new_metadata["transformed"] = True
    new_metadata["original_length"] = len(item.content)
    new_metadata["cleaned_length"] = len(content)
    
    return DataItem(
        content=content,
        metadata=new_metadata,
        sources=item.sources,
        iteration=item.iteration
    )


def example_quality_fn(item: DataItem) -> float:
    """Example quality function - scores based on content characteristics."""
    content = item.content
    
    # Basic quality metrics
    length_score = min(len(content) / 500, 1.0)  # Prefer longer content up to 500 chars
    sentence_score = min(content.count('.') + content.count('!') + content.count('?'), 10) / 10
    
    # Check for meaningful content
    has_meaningful_words = any(word in content.lower() for word in 
                              ['the', 'and', 'is', 'are', 'was', 'were', 'will', 'can'])
    meaning_score = 1.0 if has_meaningful_words else 0.3
    
    # Combine scores
    final_score = (length_score * 0.3 + sentence_score * 0.3 + meaning_score * 0.4)
    return min(final_score, 1.0)


if __name__ == "__main__":
    # Example usage
    iterator = DataIterator()
    
    # Process a sample dataset
    for item in iterator.iterate_dataset(
        "data/sample.jsonl",
        transform_fn=example_transform_fn,
        quality_fn=example_quality_fn
    ):
        print(f"Quality: {item.quality_score:.3f} | {item.content[:100]}...")
    
    # Print statistics
    stats = iterator.get_iteration_stats()
    print(f"\nIteration Stats: {json.dumps(stats, indent=2)}")
