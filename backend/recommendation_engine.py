import faiss
import json
import numpy as np

class UserInteractionTracker:
    def __init__(self):
        """
        Track user interactions with products
        """
        self.liked_products = set()
        self.disliked_products = set()
        self.interaction_embeddings = {
            'liked': [],
            'disliked': []
        }
    
    def add_interaction(self, product_id, embedding, reaction):
        """
        Record user interaction with a product

        :param product_id: ID of the product
        :param embedding: Product embedding
        :param reaction: 'like' or 'dislike'
        """
        if reaction == 'like':
            self.liked_products.add(product_id)
            self.interaction_embeddings['liked'].append(embedding)
        else:
            self.disliked_products.add(product_id)
            self.interaction_embeddings['disliked'].append(embedding)
    
    def compute_preference_vector(self):
        """
        Compute user preference vector based on interactions
        
        :return: Preference vector or None if no interactions
        """
        liked_vector = (
            np.mean(self.interaction_embeddings['liked'], axis=0) 
            if self.interaction_embeddings['liked'] 
            else None
        )
        disliked_vector = (
            np.mean(self.interaction_embeddings['disliked'], axis=0) 
            if self.interaction_embeddings['disliked'] 
            else None
        )
        
        # If both liked and disliked exist, compute weighted preference
        if liked_vector is not None and disliked_vector is not None:
            # Subtract disliked embeddings to push away from disliked products
            return liked_vector - 0.5 * disliked_vector
        
        return liked_vector or (disliked_vector and -disliked_vector)

class RecommendationEngine:
    def __init__(self, faiss_index_path, product_metadata_path):
        """
        Initialize the recommendation engine with FAISS index and product metadata
        """
        # Load FAISS index
        self.index = faiss.read_index(faiss_index_path)

        # Load product metadata
        with open(product_metadata_path, 'r') as f:
            self.product_metadata = json.load(f)

        # Create mapping between FAISS index and product IDs
        self.faiss_id_to_product_id = {
            i: item['id'] for i, item in enumerate(self.product_metadata)
        }
        self.product_id_to_faiss_id = {
            v: k for k, v in self.faiss_id_to_product_id.items()
        }
        
        # User interaction trackers
        self.user_trackers = {}
    
    def record_user_interaction(self, user_id, product_id, reaction='like'):
        """
        Record user interaction with a product
        
        :param user_id: Unique identifier for the user
        :param product_id: ID of the product interacted with
        :param reaction: 'like' or 'dislike'
        """
        # Create user tracker if not exists
        if user_id not in self.user_trackers:
            self.user_trackers[user_id] = UserInteractionTracker()
        
        # Get product embedding
        faiss_idx = self.product_id_to_faiss_id.get(product_id)
        if faiss_idx is not None:
            embedding = self.index.reconstruct(faiss_idx)
            
            # Record interaction
            self.user_trackers[user_id].add_interaction(
                product_id, 
                embedding, 
                reaction
            )
    
    def get_recommendations(self, 
                            user_id, 
                            num_recommendations=10, 
                            color_filter=None, 
                            category_filter=None):
        """
        Generate personalized and filtered recommendations
        
        :param user_id: Unique identifier for the user
        :param num_recommendations: Number of recommendations to return
        :param color_filter: List of colors to filter by
        :param category_filter: List of categories to filter by
        :return: List of filtered and ranked recommendations
        """
        # Get user tracker or create a new one
        user_tracker = self.user_trackers.get(user_id, UserInteractionTracker())
        
        # Compute user preference vector
        user_preference = user_tracker.compute_preference_vector()
        
        # If no preference, return diverse recommendations
        if user_preference is None:
            return self._get_diverse_recommendations(
                num_recommendations, 
                color_filter, 
                category_filter
            )
        
        # Perform similarity search
        distances, indices = self.index.search(
            np.array([user_preference]), 
            k=self.index.ntotal  # Search entire index
        )
        
        # Flatten the first dimension of indices and distances
        indices = indices[0]
        distances = distances[0]
        
        # Filter recommendations based on metadata and user interactions
        filtered_recommendations = []
        for i, idx in enumerate(indices):
            # Ensure idx is within the range of product metadata
            if idx >= len(self.product_metadata):
                continue
            
            product_id = self.faiss_id_to_product_id[idx]
            
            # Skip already interacted products
            if (product_id in user_tracker.liked_products or 
                product_id in user_tracker.disliked_products):
                continue
            
            product_info = next(
                item for item in self.product_metadata
                if item['id'] == product_id
            )
            
            # Apply filters
            color_match = (
                not color_filter or
                product_info.get('color', '').lower() in [c.lower() for c in color_filter]
            )
            category_match = (
                not category_filter or
                product_info.get('category', '').lower() in [c.lower() for c in category_filter]
            )
            
            # If passes filters, add to recommendations
            if color_match and category_match:
                filtered_recommendations.append({
                    'product_id': product_id,
                    'similarity_score': 1 / (1 + distances[i]),  # Convert distance to similarity
                    **product_info
                })
                
                # Stop once we have enough recommendations
                if len(filtered_recommendations) >= num_recommendations:
                    break
        
        # Sort recommendations by similarity score
        filtered_recommendations.sort(
            key=lambda x: x['similarity_score'], 
            reverse=True
        )
        
        return filtered_recommendations[:num_recommendations]
    
    def _get_diverse_recommendations(self, 
                                     num_recommendations, 
                                     color_filter=None, 
                                     category_filter=None):
        """
        Generate diverse recommendations for new users
        
        :param num_recommendations: Number of recommendations to return
        :param color_filter: List of colors to filter by
        :param category_filter: List of categories to filter by
        :return: List of diverse recommendations
        """
        # Compute global centroid
        total_vectors = self.index.ntotal
        centroids = []
        
        # Sampling strategy to get diverse recommendations
        step = max(1, total_vectors // (num_recommendations * 2))
        
        recommendations = []
        for i in range(0, total_vectors, step):
            # Get product ID and embedding
            product_id = self.faiss_id_to_product_id[i]
            product_info = next(
                item for item in self.product_metadata
                if item['id'] == product_id
            )
            
            # Apply filters
            color_match = (
                not color_filter or
                product_info.get('color', '').lower() in [c.lower() for c in color_filter]
            )
            category_match = (
                not category_filter or
                product_info.get('category', '').lower() in [c.lower() for c in category_filter]
            )
            
            # If passes filters, add to recommendations
            if color_match and category_match:
                recommendations.append({
                    'product_id': product_id,
                    **product_info
                })
                
                # Stop once we have enough recommendations
                if len(recommendations) >= num_recommendations:
                    break
        
        return recommendations

# Example usage
def main():
    # Initialize recommendation engine
    rec_engine = RecommendationEngine(
        faiss_index_path='image_vectors.index',
        product_metadata_path='processed_data.json'
    )

    # Simulate user interactions
    user_id = 'user_001'

    # User likes some products
    rec_engine.record_user_interaction(user_id, 'product_123', 'like')
    rec_engine.record_user_interaction(user_id, 'product_456', 'dislike')

    # Get recommendations
    recommendations = rec_engine.get_recommendations(
        user_id,
        num_recommendations=5,
        color_filter=['blue', 'green'],
        category_filter=['Below the Knee', 'Above the Knee']
    )

    # print([recommendation["affiliate_href"] for recommendation in recommendations])
    print(recommendations)

if __name__ == '__main__':
    main()
