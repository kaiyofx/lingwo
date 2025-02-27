<a id="readme-top"></a>
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![project_license][license-shield]][license-url]

<br />
<div align="center">
  <a href="https://github.com/kaiyofx/lingwo">
    <img src="media/banner.png" alt="Logo" width="80" height="80">
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
    <li>
      <a href="#о-проекте">О проекте</a>
    </li>
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

#<video src='media/test.mp4' width="180"/>

**Лингво** - сервис для подготовки школьников к экзамену (сочинение) по
русскому языку. Работает за счет связки модели gpt-4o и векторной базы данных [Chroma](https://github.com/chroma-core/chroma).

## Запустить в Docker
Установите [Docker](https://docs.docker.com/engine/install/)

### Запуск Лингво

1. Клонируем репозиторий
   ```sh
   git clone https://github.com/kaiyofx/lingwo.git
   ```
2. Перейдите в него
   ```sh
   cd lingwo
3. В `.env` установите ваш `OPENAI_API_KEY`
4. Запустите Docker Compose
   ```sh
   docker compose up -d
   ```

## Переменные


`OPENAI_API_KEY` - api-ключ для gpt-4o (обязательно)<br/>
`PROXY_SERVER_URL` - прокси-сервер для работы gpt-4o

## Функционал

<ol>
  <li>Предложение тем для сочинений</li>
  <li>Получение отчет о сочинении</li>
  <li>Автопродолжение и исправление  написанного сочинения</li>
  <li>Автоподсвечивание выполненности критериев</li>
</ol>

## Лицензия

`GPL-3.0`

## Контакты

Dmitry - [@kaiyofx](https://t.me/kaiyofx)

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
