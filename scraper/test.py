import json

def modify_hrefs():
    href_file = "href_data.json"

    try:
        with open(href_file, "r") as file:
            href_data = json.load(file)
    except FileNotFoundError:
        print(f"{href_file} not found.")
        exit(1)

    with open("href_data_2.json", "w") as file:
        json.dump({"Women's Clothing": href_data}, file)


def count_data():
    input_file = "product_data.json"

    try:
        with open(input_file, "r") as file:
            data = json.load(file)["Women's Clothing"]
            print(f"Categories: {len(data)}")
            total = 0;
            for field in data:
                for item in data[field]:
                    total += len(item["colors"])
                    # total += len(data[field][item]["color"])
            print(f"Images: {total}")
    except Exception as e:
        print("Error!")
        print(e)

def get_unique_categories_and_colors():
    input_file = r"./data/processed_data.json"

    with open(input_file, "r") as file:
        data = json.load(file)

    s1 = set()
    s2 = set()
    # d1 = {}
    for i in range(len(data)):
        s1.add(data[i]["category"])
        s2.add(data[i]["color"])
    #     color = data[i]["color"].lower()
    #     if color in d1:
    #         d1[color] += 1
    #     else:
    #         d1[color] = 1

    print(f"Categories: {len(s1)}")
    print(s1)
    print(f"Colors: {len(s1)}")
    print(s2)
    # print(sorted(d1.items(), key=lambda x: x[1], reverse=True))
    # s = set()
    # for k,v in d1.items():
    #     if (v >= 27):
    #         s.add(k)
    # print(s)

get_unique_categories_and_colors()
