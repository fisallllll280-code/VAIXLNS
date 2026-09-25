from .paper_treasury import demo

if __name__ == "__main__":
    import json
    print(json.dumps(demo(), indent=2, sort_keys=True))
