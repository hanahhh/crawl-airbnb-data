import subprocess
import argparse

def run_airbnb(city, price_lb, price_ub):
    command = f"scrapy crawl airbnb -a city={city} -a price_lb={price_lb} -a price_ub={price_ub} -a index={price_ub}"
    subprocess.run(command, shell=True)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, default=200000)
    parser.add_argument("--max_price", type=int, default=20000000)
    args = parser.parse_args()
    return args

def main(args):
    price_ranges = [[i, i + args.step] for i in range(0, args.max_price, args.step)]

    with open('crawl/city.txt', 'r') as file:
        lines = file.readlines()
        city = lines[0].strip()
        for price in price_ranges:
            print("_______________________________")
            print(price[0])
            print(price[1])
            run_airbnb(city, price[0], price[1])
if __name__ == "__main__":
    args = parse_args()
    main(args)