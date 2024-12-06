import numpy as np
import torch

torch.cuda.is_available()

#|%%--%%| <q0QgAWW71v|xXKdY2Y1Va>

import torch
import json
import time
import requests
from PIL import Image
from torchvision import transforms
import numpy as np

# Check and select GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Load input data
input_file = r"/home/espacio/projects/cinder/scraper/data/womens_processed_data.json"
with open(input_file, "r") as file:
    image_metadata = json.load(file)

# Load the ViT Dino model and move to GPU
model = torch.hub.load('facebookresearch/dino:main', 'dino_vits16')
model = model.to(device)
model.eval()

# Preprocessing transformations
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Function to embed images with GPU support
def get_image_embedding(image_url):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            image = Image.open(response.raw).convert('RGB')

            # Preprocess and move to GPU
            input_tensor = preprocess(image).unsqueeze(0).to(device)

            with torch.no_grad():
                embedding = model(input_tensor)

            # Move embedding back to CPU and convert to numpy
            return embedding.squeeze().cpu().numpy()

        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {image_url}: {e}")
            time.sleep(5)

# Embed images and store metadata
image_embeddings = {}
i = 0
for k,v in image_metadata.items():
    try:
        embedding = get_image_embedding(v['image_href'])
        image_embeddings[k] = {'faiss-id': i,'embedding': embedding, **v}
        i+=1

        if (i + 1) % 100 == 0:
            print(f"{i+1} images embedded")

    except Exception as e:
        print(f"Failed to process image {v['image_href']}: {e}")

# Optional: Save embeddings to a file
output_file = "image_embeddings.json"
with open(output_file, "w") as f:
    # Convert numpy arrays to lists for JSON serialization
    serializable_embeddings = [
        {**entry, 'embedding': entry['embedding'].tolist()}
        for entry in image_embeddings
    ]
    json.dump(serializable_embeddings, f)

output_file = "product_metadata.json"
with open(output_file, "w") as f:
    image_embeddings = {k:v for k,v in image_embeddings.items() if k != "embedding"}
    json.dump(serializable_embeddings, f)

print(f"Saved {len(image_embeddings)} image embeddings to {output_file}")
#|%%--%%| <xXKdY2Y1Va|0p1ZMMQG35>

import faiss
import numpy as np

# Prepare FAISS index
dimension = 384  # Dimension of embeddings
index = faiss.IndexFlatL2(dimension)

# Add embeddings to the index
embeddings = np.array([item['embedding'] for item in image_embeddings])
index.add(embeddings)

# Save the index
faiss.write_index(index, 'image_vectors.index')

