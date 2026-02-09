<a id="readme-top"></a>
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![project_license][license-shield]][license-url]

<br />
<div align="center">
  <a href="https://lingwo.ru">
    <img src="media/banner.png" alt="Logo">
  </a>
<h3 align="center">Лингво</h3>

  <p align="center">
    ИИ-репетитор для подготовки к экзамену по русскому языку
    <br />
    <a href="https://lingwo.ru">Демо</a>
    &middot;
    <a href="https://github.com/kaiyofx/lingwo/issues/new?labels=bug&template=bug-report---.md">Сообщить об ошибке</a>
  </p>
</div>

<details>
  <summary>Содержание</summary>
  <ol>
    <li><a href="#о-проекте">О проекте</a></li>
    <li>
      <a href="#запустить-в-docker">Запустить в Docker</a>
      <ul>
        <li><a href="#запуск-лингво">Запуск Лингво</a></li>
        <li><a href="#переменные">Переменные</a></li>
      </ul>
    </li>
    <li><a href="#функционал">Функционал</a></li>
    <li><a href="#лицензия">Лицензия</a></li>
    <li><a href="#контакты">Контакты</a></li>
  </ol>
</details>

## О проекте

**Лингво** — сервис для подготовки школьников к сочинению по русскому языку. Использует связку модели gpt-4o и векторной базы данных [Chroma](https://github.com/chroma-core/chroma).

Стек: фронтенд (Nuxt 3), API (FastAPI), сервис авторизации (Django), PostgreSQL, ChromaDB.

## Запустить в Docker

Установите [Docker](https://docs.docker.com/engine/install/).

### Запуск Лингво

1. Клонируйте репозиторий:
   ```sh
   git clone https://github.com/kaiyofx/lingwo.git
   ```
2. Перейдите в каталог проекта:
   ```sh
   cd lingwo
   ```
3. Создайте файл `.env` в корне и задайте переменные (см. раздел «Переменные»). Обязательно укажите `OPENAI_API_KEY`.
4. Запустите все сервисы:
   ```sh
   docker compose up -d
   ```

Порядок запуска: сначала поднимаются **PostgreSQL** и **Chroma**, затем после готовности Chroma выполняется **chroma-init** (инициализация коллекций), после его успешного завершения стартуют **API** и **frontend** (Nuxt). Сервис **auth** можно подключать к той же БД (см. переменные).

После запуска:
- фронтенд: http://localhost:3000  
- API: http://localhost:8001  
- auth: http://localhost:8000  
- Chroma: http://localhost:8002  

### Переменные

**API и модель:**
- `OPENAI_API_KEY` — API-ключ для gpt-4o (обязательно)
- `PROXY_SERVER_URL` — прокси-сервер для работы gpt-4o (по желанию)

**PostgreSQL** (для сервисов `pg`, `api`; при использовании auth с той же БД — и для auth):
- `PG_USER` — пользователь (по умолчанию `postgres`)
- `PG_PASSWORD` — пароль (по умолчанию `1234`)
- `PG_NAME` — имя БД (по умолчанию `lingwo`)
- Для auth при запуске через Docker: `PG_HOST=pg`, `PG_PORT=5432`

Остальные переменные для auth (email, Redis, ключи и т.д.) задаются в `.env` по необходимости.

## Функционал

- Предложение тем для сочинений
- Получение отчёта по сочинению
- Автопродолжение и исправление написанного сочинения
- Автоподсвечивание выполненности критериев

## Лицензия

`GPL-3.0`

## Контакты

- Почта: [contact@lingwo.ru](mailto:contact@lingwo.ru)
- Telegram: [@kaiyofx](https://t.me/kaiyofx)

[contributors-shield]: https://img.shields.io/github/contributors/kaiyofx/lingwo.svg?style=for-the-badge
[contributors-url]: https://github.com/kaiyofx/lingwo/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/kaiyofx/lingwo.svg?style=for-the-badge
[forks-url]: https://github.com/kaiyofx/lingwo/network/members
[stars-shield]: https://img.shields.io/github/stars/kaiyofx/lingwo.svg?style=for-the-badge
[stars-url]: https://github.com/kaiyofx/lingwo/stargazers
[issues-shield]: https://img.shields.io/github/issues/kaiyofx/lingwo.svg?style=for-the-badge
[issues-url]: https://github.com/kaiyofx/lingwo/issues
[license-shield]: https://img.shields.io/github/license/kaiyofx/lingwo.svg?style=for-the-badge
[license-url]: https://github.com/kaiyofx/lingwo/blob/main/LICENSE
[product-video]: media/test.mp4
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
