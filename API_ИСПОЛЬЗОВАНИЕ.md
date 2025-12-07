# Руководство по использованию GraphQL API для книжного сайта

## Обзор

Это GraphQL API для управления библиотекой книг, аудиокниг, авторов, коллекций и связанного контента. API поддерживает операции чтения (Query) и изменения данных (Mutation).

## Основные типы данных

### Книги (Book)
- Уникальный идентификатор (`uuid`)
- Название, slug, аннотация
- Изображение, EPUB файл
- Авторы, категории, теги, коллекции
- Даты публикации, возрастные ограничения

### Аудиокниги (Audiobook)
- Аналогично книгам, но с треками (`audiobookTrack`)
- Длительность в секундах

### Авторы (Author)
- Имя, фамилия, отчество
- Изображение, аннотация
- Связанные книги и аудиокниги

### Коллекции (Collection)
- Группировка книг и аудиокниг
- Порядок элементов (`orderUuids`)

---

## Примеры запросов (Query)

### 1. Получить список книг с фильтрацией

```graphql
query GetBooks {
  books(body: {
    isActive: true
    limit: 20
    page: 1
    titleSort: "asc"
  }) {
    uuid
    name
    slug
    annotation
    image {
      url
    }
    authors(limit: 5) {
      uuid
      firstName
      lastName
    }
    categories {
      uuid
      name
    }
  }
}
```

### 2. Получить конкретную книгу по UUID или slug

```graphql
query GetBook {
  book(body: {
    uuid: "book-uuid-here"
    # или
    # slug: "book-slug"
  }) {
    uuid
    name
    annotation
    annotationHTML
    image {
      url
      name
    }
    epub {
      url
    }
    authors {
      uuid
      firstName
      lastName
      patronymic
    }
    categories {
      uuid
      name
      slug
    }
    tags {
      uuid
      name
    }
    collections {
      uuid
      name
    }
    bookSections {
      uuid
      name
      href
      order
    }
    publicationDate
    ageLimit
  }
}
```

### 3. Поиск книг по авторам

```graphql
query SearchBooksByAuthors {
  books(body: {
    authors: ["author-uuid-1", "author-uuid-2"]
    isActive: true
    limit: 10
  }) {
    uuid
    name
    authors {
      firstName
      lastName
    }
  }
}
```

### 4. Получить книги с пагинацией

```graphql
query GetBooksWithPagination {
  booksWithPagination(body: {
    isActive: true
    limit: 20
    page: 1
    titleSort: "desc"
  }) {
    books {
      uuid
      name
      slug
      image {
        url
      }
    }
    pageInfo {
      totalCount
      perPage
      totalPage
    }
  }
}
```

### 5. Получить автора с его книгами

```graphql
query GetAuthor {
  author(body: {
    uuid: "author-uuid"
    # или
    # slug: "author-slug"
  }) {
    uuid
    firstName
    lastName
    patronymic
    annotation
    image {
      url
    }
    books(limit: 10, page: 1) {
      uuid
      name
      slug
      image {
        url
      }
    }
    audiobooks(limit: 10, page: 1) {
      uuid
      name
      slug
    }
  }
}
```

### 6. Получить коллекцию с книгами

```graphql
query GetCollection {
  collection(body: {
    uuid: "collection-uuid"
  }) {
    uuid
    name
    annotation
    image {
      url
    }
    books(limit: 50, page: 1) {
      uuid
      name
      slug
      image {
        url
      }
    }
    audiobooks(limit: 50, page: 1) {
      uuid
      name
      slug
    }
    orderUuids
  }
}
```

### 7. Универсальный поиск

```graphql
query UniversalSearch {
  search(body: {
    text: "название книги или автора"
    category: ["category-uuid-1"]
    tag: ["tag-uuid-1"]
    author: ["author-uuid-1"]
    ageLimit: ["12+", "16+"]
    limit: 20
    page: 1
  }) {
    books {
      uuid
      name
      slug
    }
    audiobooks {
      uuid
      name
      slug
    }
    authors {
      uuid
      firstName
      lastName
    }
    articles {
      uuid
      name
      slug
    }
  }
}
```

### 8. Получить аудиокнигу с треками

```graphql
query GetAudiobook {
  audiobook(body: {
    uuid: "audiobook-uuid"
  }) {
    uuid
    name
    annotation
    duration
    image {
      url
    }
    audiobookTrack {
      uuid
      name
      order
      duration
      audio {
        url
      }
    }
    authors {
      firstName
      lastName
    }
  }
}
```

---

## Примеры мутаций (Mutation)

### 1. Создать книгу

```graphql
mutation CreateBook {
  createBook(body: {
    name: "Название книги"
    slug: "nazvanie-knigi"
    annotation: "Аннотация книги"
    annotationHTML: "<p>Аннотация в HTML</p>"
    image: "https://example.com/image.jpg"
    isActive: true
    ageLimit: "12+"
    publicationDate: "2025-01-01T00:00:00Z"
    isGlobalVersion: true
    externalUuid: "external-id-123"
  }) {
    uuid
    name
    slug
  }
}
```

### 2. Обновить книгу

```graphql
mutation UpdateBook {
  updateBook(
    uuid: "book-uuid"
    body: {
      name: "Обновленное название"
      annotation: "Новая аннотация"
      isActive: false
    }
  ) {
    uuid
    name
    annotation
    isActive
  }
}
```

### 3. Добавить автора к книге

```graphql
mutation AddAuthorToBook {
  addBookAuthor(body: {
    bookUuid: "book-uuid"
    authorUuid: "author-uuid"
    order: 1
  }) {
    uuid
    firstName
    lastName
  }
}
```

### 4. Добавить тег к книге

```graphql
mutation AddTagToBook {
  addBookTag(body: {
    book: "book-uuid"
    tag: "tag-uuid"
  }) {
    uuid
    name
  }
}
```

### 5. Добавить книгу в коллекцию

```graphql
mutation AddBookToCollection {
  addBookCollection(body: {
    collectionUuid: "collection-uuid"
    bookUuid: "book-uuid"
    order: 5
  }) {
    uuid
    name
    books {
      uuid
      name
    }
  }
}
```

### 6. Создать автора

```graphql
mutation CreateAuthor {
  createAuthor(body: {
    firstName: "Иван"
    lastName: "Иванов"
    patronymic: "Иванович"
    annotation: "Биография автора"
    image: "https://example.com/author.jpg"
    type: 1
    isActive: true
    order: 1
    slug: "ivanov-ivan"
  }) {
    uuid
    firstName
    lastName
  }
}
```

### 7. Создать коллекцию

```graphql
mutation CreateCollection {
  createCollection(body: {
    name: "Название коллекции"
    slug: "nazvanie-kollekcii"
    annotation: "Описание коллекции"
    image: "https://example.com/collection.jpg"
    isActive: true
    order: 1
  }) {
    uuid
    name
    slug
  }
}
```

### 8. Создать раздел книги (BookSection)

```graphql
mutation CreateBookSection {
  createBookSection(body: {
    bookUuid: "book-uuid"
    name: "Глава 1"
    href: "#chapter1"
    path: "/book/chapter1"
    order: 1
    level: 1
    isShow: true
    isActive: true
    part: 0.1
    offset: 0
  }) {
    uuid
    name
    order
  }
}
```

---

## Работа с коллекциями пользователей

### Получить коллекции пользователя

```graphql
query GetUserCollections {
  collectionsUsers {
    uuid
    name
    orderUuids
    books(limit: 50, page: 1) {
      uuid
      name
    }
    audiobooks(limit: 50, page: 1) {
      uuid
      name
    }
  }
}
```

### Действия с коллекциями пользователей

```graphql
mutation ActionUserCollection {
  actionBookCollectionUsers(body: [
    {
      uuid: "action-uuid-1"
      actionType: 1  # 1 - добавить, 2 - удалить, и т.д.
      createdAt: "2025-01-01T00:00:00Z"
      type: 1  # Тип элемента
      collectionUuid: "collection-uuid"
      collectionType: 1
    }
  ])
}
```

---

## Работа с профилем и прогрессом

### Получить профиль пользователя

```graphql
query GetProfile {
  profile {
    uuid
    fullName
    username
    email
    image {
      url
    }
    progresses {
      uuid
      book {
        uuid
        name
      }
      audiobook {
        uuid
        name
      }
      totalProgression
    }
    collections {
      uuid
      name
    }
  }
}
```

### Получить прогресс чтения книги

```graphql
query GetBookProgress {
  progress(bookUuid: "book-uuid") {
    uuid
    totalProgression
    info
    book {
      uuid
      name
    }
  }
}
```

---

## Работа с категориями и тегами

### Получить категории

```graphql
query GetCategories {
  categories(body: {
    typeView: ALL  # или BOOK, или MEDIA
  }) {
    uuid
    name
    slug
    image {
      url
    }
  }
}
```

### Получить теги

```graphql
query GetTags {
  tags(body: {
    uuids: ["tag-uuid-1", "tag-uuid-2"]
  }) {
    uuid
    name
    slug
    tagCategory {
      uuid
      name
    }
  }
}
```

---

## Работа со статьями

### Получить статьи

```graphql
query GetArticles {
  articles(body: {
    isActive: "true"
    limit: 20
    page: 1
    search: "поисковый запрос"
  }) {
    uuid
    name
    slug
    annotation
    preview {
      url
    }
    createdAt
  }
}
```

### Получить статью с блоками контента

```graphql
query GetArticle {
  articleOne(body: {
    uuid: "article-uuid"
  }) {
    uuid
    name
    contentBlock {
      uuid
      type
      content
      order
      book {
        uuid
        name
      }
      audiobook {
        uuid
        name
      }
    }
  }
}
```

---

## Практические советы

### 1. Используйте пагинацию для больших списков
Всегда указывайте `limit` и `page` при запросе списков, чтобы не перегружать ответ.

### 2. Фильтруйте по `isActive`
Для клиентских запросов используйте `isActive: true`, чтобы показывать только активный контент.

### 3. Используйте slug для SEO
Slug используется для создания читаемых URL на сайте.

### 4. Порядок элементов
Используйте поле `order` и `orderUuids` для управления порядком отображения элементов.

### 5. Внешние идентификаторы
Поле `externalUuid` полезно для интеграции с внешними системами.

### 6. Возрастные ограничения
Фильтруйте контент по `ageLimit` для соответствия возрастным ограничениям.

---

## Типичные сценарии использования

### Сценарий 1: Главная страница
- Получить активные коллекции
- Получить последние книги
- Получить популярных авторов

### Сценарий 2: Страница книги
- Получить информацию о книге
- Получить авторов книги
- Получить связанные книги из коллекций
- Получить разделы книги (оглавление)

### Сценарий 3: Каталог
- Поиск с фильтрами (категории, теги, авторы)
- Сортировка и пагинация
- Фильтрация по возрастным ограничениям

### Сценарий 4: Личный кабинет
- Получить профиль пользователя
- Получить прогресс чтения
- Управление коллекциями пользователя

---

## Обработка ошибок

При работе с API обращайте внимание на:
- Обязательные поля (помечены `!` в схеме)
- Формат дат (`DateTime` - ISO 8601)
- Валидность UUID
- Существование связанных сущностей перед созданием связей

---

## Пример полного запроса для страницы книги

```graphql
query GetBookPage($bookUuid: String!) {
  book(body: { uuid: $bookUuid }) {
    uuid
    name
    slug
    annotation
    annotationHTML
    image {
      url
      name
    }
    epub {
      url
    }
    ageLimit
    publicationDate
    authors {
      uuid
      firstName
      lastName
      patronymic
      slug
      image {
        url
      }
    }
    categories {
      uuid
      name
      slug
    }
    tags {
      uuid
      name
      slug
    }
    collections {
      uuid
      name
      slug
    }
    bookSections {
      uuid
      name
      href
      order
      level
      isShow
    }
    articles {
      uuid
      name
      slug
    }
    tests {
      uuid
      description
    }
  }
  
  # Получить связанные книги из коллекций
  collections(body: {
    uuids: ["collection-uuid-1", "collection-uuid-2"]
  }) {
    uuid
    name
    books(limit: 5) {
      uuid
      name
      slug
      image {
        url
      }
    }
  }
}
```

---

Это API предоставляет полный функционал для работы с книжным каталогом, включая поиск, фильтрацию, управление контентом и пользовательскими данными.

