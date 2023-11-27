# ВШЭ МОВС 2023 курс ML, Гераськина Надежда
## Домашнее задание №1 


В данной работе были на практике пройдены все этапы разработки ML модели:
1. Первичный анализ данных (EDA);
2. Предобработка данных;
3. Обучение моделей линейной регрессии с различными гиперпараметрами и регуляризаторами;
4. Поиск оптимальных гиперпараметров (GridSearch);
5. Feature engineering;
6. Создание сервиса, который выдает предсказания модели для одного или нескольких экземпляров (машин) (на FastAPI).


Было выявлено несколько **интересных зависимостей** в данных:
* больше всего с целевой переменной (selling price) коррелирует max power - это логично, чем мощнее машина, тем она дороже;
* среди признаков (фич) между собой больше всего коррелируют следующие пары: torque - max_power, engine - max_power, torque - engine, что также логично, это показатели мощности (простите за жаргон, крутости) машины;
* есть признаки, которые возможно связаны с целевой переменной нелинейно (year, km_driven);
* дополнительно я обнаружила корреляцию объема двигателя (engine) и крутящего момента (torque), а также объема двигателя (engine) и расхода топлива (mileage).


Данные зависимости присутствуют как в обучающем, так и в тестовом датасете, что свидетельствует об однородности train и test данных (или по простому, что тест похож на трейн)


**Наибольший буст** в качестве модели дало добавление закодированных (OneHotEncoding) категориальных переменных и создание новых переменых (feature engineering)

В feature engineering были дополнительно проанализированы следующие зависимости и добавлены следующие признаки:
* добавлены year_squared и km_driven_squared;
* удален один выброс по полю max_torque_rpm;
* проанализированы выбросы в seats и selling price, эти данные оказались ействительно важными и нужными, они не были удалены;
* отлогарифмированы torque и engine, так как они имели далеко не нормальное распределение (это не сильно помогло, но наблюдался прирост в качестве обученной модели).

**Скрины-демонстрация работы сервиса**:
![Описание картинки](/pics/predict_item.png "Подпись под картинкой")
![Описание картинки](/pics/predict_items_2.png "Подпись под картинкой")


**Что не удалось сделать:**
1. В сервисе реализовать импорт и экспорт файлов (вышло только при помощи данных pydantic классов)
2. С помощью Gridsearch улучшить качество модели (что удивительно, но факт)
3. Посчитать кол-во лошадей на литр бензина
