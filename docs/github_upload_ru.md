# Пошаговая загрузка проекта на GitHub без терминала

1. Зайди на https://github.com и войди в свой аккаунт.
2. Справа сверху нажми **+** → **New repository** (или на главной зелёную кнопку **New**).
3. В поле **Repository name** напиши `checkout-ab-test`.
4. В поле **Description** вставь `Product analytics A/B experiment: SQL, Python, statistical testing and business insights (synthetic data)`.
5. Выбери **Public**, чтобы работодатель мог открыть ссылку.
6. НЕ ставь галочку **Add a README file**, НЕ добавляй `.gitignore` или лицензию при создании: они уже лежат в архиве.
7. Нажми **Create repository**.
8. На компьютере найди скачанный ZIP → правая кнопка → **Извлечь всё** (Windows). Открой полученную папку `checkout-ab-test`.
9. На пустой странице репозитория нажми **uploading an existing file**. Если этой ссылки нет, выбери **Add file** → **Upload files**.
10. Перетащи **содержимое папки** `checkout-ab-test` на область загрузки GitHub (README.md, data, src, sql и т. д.). НЕ перетаскивай ZIP-файл как единственный файл. Если браузер не принимает несколько директорий, перетащи их по одной на ту же страницу загрузки. Убедись, что в списке путей есть `data/checkout_experiment_synthetic.csv`, `notebooks/ab_test_walkthrough.ipynb`, `src/analysis.py`, `README.md`.
11. В поле **Commit message** напиши `Add reproducible checkout A/B test portfolio project`.
12. Подтверди загрузку кнопкой **Commit changes** (или **Propose changes**, если она отображается, и заверши предложенный интерфейс GitHub).
13. Открой главную страницу репозитория, проверь структуру папок и отображение README и двух графиков.
14. Скопируй ссылку вида `https://github.com/ТВОЙ_ЛОГИН/checkout-ab-test` и добавь в резюме.

**Примечание:** GitHub иногда меняет подписи кнопок. Официальная инструкция: https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository

**Если не получается:** отправь скриншот того, что видишь; разберём конкретно этот шаг.
