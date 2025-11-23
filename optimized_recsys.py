import heapq
import time
import random
import sys
from functools import lru_cache

class OptimizedUserItemGraph:
    """
    Phase 3 Implementation:
    - Uses Integer Mapping to reduce memory overhead of strings.
    - Uses sets for fast O(1) lookups.
    """
    def __init__(self):
        # Internal Storage (Integers)
        self.user_to_items = {} # { int_uid: set(int_iids) }
        self.item_to_users = {} # { int_iid: set(int_uids) }
        
        # Mappings (String <-> Integer)
        self.str_to_int_user = {}
        self.int_to_str_user = {}
        self.user_counter = 0
        
        self.str_to_int_item = {}
        self.int_to_str_item = {}
        self.item_counter = 0

    def _get_user_id(self, user_str):
        """Maps string user ID to internal integer ID."""
        if user_str not in self.str_to_int_user:
            uid = self.user_counter
            self.str_to_int_user[user_str] = uid
            self.int_to_str_user[uid] = user_str
            self.user_counter += 1
        return self.str_to_int_user[user_str]

    def _get_item_id(self, item_str):
        """Maps string item ID to internal integer ID."""
        if item_str not in self.str_to_int_item:
            iid = self.item_counter
            self.str_to_int_item[item_str] = iid
            self.int_to_str_item[iid] = item_str
            self.item_counter += 1
        return self.str_to_int_item[item_str]

    def add_interaction(self, user_str, item_str):
        """Adds an interaction using optimized integer IDs."""
        uid = self._get_user_id(user_str)
        iid = self._get_item_id(item_str)

        self.user_to_items.setdefault(uid, set()).add(iid)
        self.item_to_users.setdefault(iid, set()).add(uid)

    def get_user_items(self, user_str):
        """Returns set of item integers for a user string."""
        if user_str not in self.str_to_int_user:
            return set()
        uid = self.str_to_int_user[user_str]
        return self.user_to_items.get(uid, set())

    def get_item_users(self, item_int):
        """Returns set of user integers for an item integer."""
        return self.item_to_users.get(item_int, set())

class OptimizedRecommendationEngine:
    def __init__(self, graph):
        self.graph = graph

    @lru_cache(maxsize=10000)
    def compute_similarity(self, item_a_int, item_b_int):
        """
        Phase 3 Optimization: LRU Caching
        Caches similarity scores for frequently compared items.
        """
        users_a = self.graph.get_item_users(item_a_int)
        users_b = self.graph.get_item_users(item_b_int)
        
        if not users_a or not users_b:
            return 0.0
            
        intersection = len(users_a & users_b) # Set intersection is optimized in C
        union = len(users_a | users_b)
        
        return intersection / union if union > 0 else 0.0

    def recommend(self, user_str, k=5):
        """
        Phase 3 Optimization: Candidate Pruning
        Only scores items that share at least one user with the target items.
        """
        user_items_ints = self.graph.get_user_items(user_str)
        if not user_items_ints:
            return []

        scores = {}
        
        # 1. Candidate Generation (The Pruning Step)
        # Instead of iterating all items, find only potentially relevant ones
        candidate_items = set()
        
        for my_item in user_items_ints:
            # Get users who bought what I bought
            related_users = self.graph.get_item_users(my_item)
            for other_user in related_users:
                # Get what those other users bought
                their_items = self.graph.user_to_items[other_user]
                candidate_items.update(their_items)
        
        # Remove items I already bought
        candidate_items -= user_items_ints

        # 2. Scoring (Only on candidates)
        for candidate in candidate_items:
            score_sum = 0
            for my_item in user_items_ints:
                sim = self.compute_similarity(my_item, candidate)
                score_sum += sim
            scores[candidate] = score_sum

        # 3. Ranking using Heap
        top_k_ints = heapq.nlargest(k, scores.items(), key=lambda x: x[1])
        
        # Convert back to Strings for the user
        return [(self.graph.int_to_str_item[iid], score) for iid, score in top_k_ints]

# --- Stress Testing & Validation ---

def run_stress_test():
    print("--- Starting Stress Test (Phase 3) ---")
    
    graph = OptimizedUserItemGraph()
    engine = OptimizedRecommendationEngine(graph)

    # 1. Data Generation
    NUM_USERS = 10000
    NUM_ITEMS = 1000
    NUM_INTERACTIONS = 100000
    
    print(f"Generating {NUM_INTERACTIONS} interactions...")
    start_time = time.time()
    
    for _ in range(NUM_INTERACTIONS):
        u = f"User{random.randint(0, NUM_USERS)}"
        i = f"Item{random.randint(0, NUM_ITEMS)}"
        graph.add_interaction(u, i)
        
    end_time = time.time()
    print(f"Ingestion Time: {end_time - start_time:.4f} seconds")
    print(f"Memory Size (User Map): {sys.getsizeof(graph.user_to_items)} bytes")

    # 2. Recommendation Performance
    print("\nBenchmarking Recommendations...")
    test_user = f"User{random.randint(0, NUM_USERS)}"
    
    start_time = time.time()
    recs = engine.recommend(test_user, k=5)
    end_time = time.time()
    
    print(f"Recommendation Time for {test_user}: {end_time - start_time:.4f} seconds")
    print(f"Recommendations: {recs}")
    
    # 3. Cache Hit Verification
    # Run same query again to trigger cache
    start_time = time.time()
    recs = engine.recommend(test_user, k=5)
    end_time = time.time()
    print(f"Cached Recommendation Time: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    run_stress_test()
