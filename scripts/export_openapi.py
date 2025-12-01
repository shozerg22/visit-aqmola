import json
from app import app
from fastapi.openapi.utils import get_openapi


def main():
    spec = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    with open('openapi.json', 'w', encoding='utf-8') as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    print('openapi.json exported')


if __name__ == '__main__':
    main()
