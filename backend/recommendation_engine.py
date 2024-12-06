import faiss
import json
import numpy as np


class UserInteractionTracker:
    def __init__(self):
        self.liked_products = set()
        self.disliked_products = set()
        self.interaction_embeddings = {"liked": [], "disliked": []}

    def add_interaction(self, product_id, embedding, reaction):
        if reaction == "like":
            self.liked_products.add(product_id)
            self.interaction_embeddings["liked"].append(embedding)
        else:
            self.disliked_products.add(product_id)
            self.interaction_embeddings["disliked"].append(embedding)

    def compute_preference_vector(self):
        liked_vector = (
            np.mean(self.interaction_embeddings["liked"], axis=0)
            if self.interaction_embeddings["liked"]
            else None
        )
        disliked_vector = (
            np.mean(self.interaction_embeddings["disliked"], axis=0)
            if self.interaction_embeddings["disliked"]
            else None
        )

        if liked_vector is not None and disliked_vector is not None:
            return liked_vector - 0.5 * disliked_vector
        elif liked_vector is not None:
            return liked_vector
        elif disliked_vector is not None:
            return -disliked_vector
        return None


class RecommendationEngine:
    def __init__(self, faiss_index_path, product_metadata_path):
        self.index = faiss.read_index(faiss_index_path)

        with open(product_metadata_path, "r") as f:
            self.product_metadata = json.load(f)

        self.faiss_id_to_product_id = {
            i: item["id"] for i, item in enumerate(self.product_metadata.keys())
        }
        self.product_id_to_faiss_id = {
            v: k for k, v in self.faiss_id_to_product_id.items()
        }

        self.user_trackers = {}

    def record_user_interaction(self, user_id, product_id, reaction="like"):
        if user_id not in self.user_trackers:
            self.user_trackers[user_id] = UserInteractionTracker()

        faiss_idx = self.product_id_to_faiss_id.get(product_id)
        if faiss_idx is not None:
            embedding = self.index.reconstruct(faiss_idx)

            # Record interaction
            self.user_trackers[user_id].add_interaction(product_id, embedding, reaction)

    def get_recommendations(
        self, user_id, num_recommendations=10, color_filter=None, category_filter=None
    ):
        user_tracker = self.user_trackers.get(user_id, UserInteractionTracker())

        user_preference = user_tracker.compute_preference_vector()

        if user_preference is None:
            return self._get_diverse_recommendations(
                num_recommendations, color_filter, category_filter
            )

        distances, indices = self.index.search(
            np.array([user_preference]), k=self.index.ntotal  # Search entire index
        )

        indices = indices[0]
        distances = distances[0]

        filtered_recommendations = []
        for i, idx in enumerate(indices):
            if idx >= len(self.product_metadata):
                continue

            product_id = self.faiss_id_to_product_id[idx]

            if (
                product_id in user_tracker.liked_products
                or product_id in user_tracker.disliked_products
            ):
                continue

            # product_info = next(
            #     item for item in self.product_metadata if item["id"] == product_id
            # )
            product_info = self.product_metadata[i]

            # apply filters
            color_match = not color_filter or product_info.get("color", "").lower() in [
                c.lower() for c in color_filter
            ]
            category_match = not category_filter or product_info.get(
                "category", ""
            ).lower() in [c.lower() for c in category_filter]

            if color_match and category_match:
                filtered_recommendations.append(
                    {
                        "similarity_score": 1
                        / (1 + distances[i]),
                        **product_info,
                    }
                )

                if len(filtered_recommendations) >= num_recommendations:
                    break

        filtered_recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)

        return filtered_recommendations[:num_recommendations]

    def _get_diverse_recommendations(
        self, num_recommendations, color_filter=None, category_filter=None
    ):
        total_vectors = self.index.ntotal

        step = max(1, total_vectors // (num_recommendations * 2))

        recommendations = []
        for i in range(0, total_vectors, step):
            product_id = self.faiss_id_to_product_id[i]
            product_info = self.product_metadata[i]

            color_match = not color_filter or product_info.get("color", "").lower() in [
                c.lower() for c in color_filter
            ]
            category_match = not category_filter or product_info.get(
                "category", ""
            ).lower() in [c.lower() for c in category_filter]

            if color_match and category_match:
                recommendations.append({"product_id": product_id, **product_info})

                if len(recommendations) >= num_recommendations:
                    break

        return recommendations


def main():
    rec_engine = RecommendationEngine(
        faiss_index_path="image_vectors.index",
        product_metadata_path="processed_data.json",
    )

    user_id = "user_001"

    rec_engine.record_user_interaction(user_id, "product_123", "like")
    rec_engine.record_user_interaction(user_id, "product_456", "dislike")

    recommendations = rec_engine.get_recommendations(
        user_id,
        num_recommendations=5,
        color_filter=["navy blue", "green"],
        category_filter=["Below the Knee", "Above the Knee"],
    )

    print([recommendation["affiliate_href"] for recommendation in recommendations])
    # print(recommendations)


if __name__ == "__main__":
    main()
