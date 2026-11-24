# Система моніторингу обладнання (ЛР 15–18)

## Варіант 19

- **Ситуація:** Дослідна компостна станція
- **Пристрої:** Компост центр; Компост край; Двір
- **Пошук (q):** Компост
- **Поріг:** 60 °C

## Середовище

- Python: (вкажіть вашу точну версію з `python -VV`)
- Django: 6.1.2

## Запуск

1. `py -3.12 -m venv .venv`
2. `.venv\Scripts\python.exe -m pip install -r requirements.txt`
3. `.venv\Scripts\python.exe manage.py migrate`
4. `.venv\Scripts\python.exe manage.py check`
5. `.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000`
