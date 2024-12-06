import json

# Load the product data
with open('./data/womens_product_data.json', 'r') as file:
    data = json.load(file)

# Extract necessary data
image_metadata = {}  # To store extracted image URLs and metadata
id = 1
for category, products in data["Women's Clothing"].items():
    for product in products:
        title = product['title']
        price = product['price']
        product_info = product['product_information']
        about_item = product['about_item']

        for color, color_data in product['colors'].items():
            # Get the top image (assuming it's the first one)
            color = color.lower()
            if color not in ['off white', 'pink', 'unknown', 'yellow', 'black', 'white', 'wine', 'brown', 'multicolour', 'olive', 'purple', 'green', 'red', 'beige', 'grey', 'maroon', 'peach', 'navy blue', 'magenta', 'rust', 'mustard', 'navy', 'orange', 'blue', 'dark blue', 'sky blue', 'teal']:
                color = "unknown"
            top_image = color_data['images'][0]
            image_metadata[id] = {
                'id': f"product_{id}",
                'affiliate_href': color_data["affiliate_href"],
                'category': category,
                'title': title,
                'price': price,
                'product_information': product_info,
                'about_item': about_item,
                'color': color,
                'image_href': top_image['href'],
                'image_alt': top_image['alt']
            }
            id += 1

with open("./data/womens_processed_data.json", "w") as file:
    json.dump(image_metadata, file)
