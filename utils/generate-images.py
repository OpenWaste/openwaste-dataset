import argparse
import os
import re
import time
from argparse import Namespace
from collections import defaultdict
from datetime import datetime

import pandas as pd
import requests
from openai import OpenAI

generated_count_column_name = '_generated_image_count_'


def generate_image(prompt: str, model: str = "dall-e-2", size: str = '512x512', path: str = './images',
                   prompt_id: str = 'Pn', count: int = 1) -> None:
    client = OpenAI()
    response = client.images.generate(
        prompt=prompt,
        model=model,
        size=size,
        quality="standard",
        n=count
    )

    image_urls = [i.url for i in response.data]
    save_images(path, prompt_id, image_urls)


def save_images(path: str, prompt_id: str, image_urls: list[str]) -> None:
    responses = [requests.get(url) for url in image_urls]
    for response in responses:
        time_str = datetime.now().strftime('%Y%m%d_%H%M%S.%f')
        img_name = f'image_{prompt_id}_{time_str}.png'
        img_path = path + '/' + img_name
        with open(img_path, 'wb') as f:
            f.write(response.content)


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompts_file", help="Two-column CSV file for prompts. First column is for the "
                                             "category, and the second column is for the prompt.")
    return parser.parse_args()


def get_prompts_df(prompts_file: str) -> pd.DataFrame:
    df = pd.read_csv(prompts_file)
    return df


def create_category_directories(df: pd.DataFrame) -> None:
    categories = df['Category'].str.strip().unique().tolist()

    for category in categories:
        os.makedirs('images/' + category, exist_ok=True)


def populate_generated_image_counts(df: pd.DataFrame) -> None:
    images_dir = "./images"
    category_names = [name for name in os.listdir(images_dir) if os.path.isdir(os.path.join(images_dir, name))]
    image_name_pattern = "image_(?P<ID>[^_]+)_[_0-9.]+.png"
    df[generated_count_column_name] = 0

    for category_name in category_names:
        category_image_path = os.path.join(images_dir, category_name)
        image_names = [name for name in os.listdir(category_image_path)
                       if os.path.isfile(os.path.join(category_image_path, name))]

        count = defaultdict(int)
        for image_name in image_names:
            match = re.search(image_name_pattern, image_name)
            if match:
                prompt_id = match.groupdict()['ID']
                count[prompt_id] += 1

        for prompt_id, num in count.items():
            df.loc[(df['Category'] == category_name) & (df['ID'] == prompt_id), [generated_count_column_name]] \
                = int(num)

    df[generated_count_column_name] = pd.to_numeric(df[generated_count_column_name], downcast='integer')


def test_sleep(df: pd.DataFrame, time_step: int) -> None:
    images_to_generate = df[df['Count'] > df[generated_count_column_name]]

    for _, row in images_to_generate.iterrows():
        category, prompt, prompt_id, count, generated_count = (row['Category'], row['Prompt'], row['ID'], row['Count'],
                                                               row[generated_count_column_name])
        path = f'images/{category}'
        while generated_count < count:
            to_generate_count = min(5, count-generated_count)
            print(f'Generating {to_generate_count} images for category: {category} with prompt ID: {prompt_id} ...',
                  end='')
            generate_image(prompt, prompt_id=prompt_id, path=path, count=to_generate_count)
            print(' Done.')
            generated_count += to_generate_count
            if generated_count < count:
                time.sleep(time_step)


def main():
    args = parse_args()
    prompts_file = args.prompts_file

    df = get_prompts_df(prompts_file)
    create_category_directories(df)
    populate_generated_image_counts(df)
    test_sleep(df, 60)


if __name__ == '__main__':
    main()
