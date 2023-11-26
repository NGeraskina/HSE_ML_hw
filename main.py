from io import BytesIO

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import pandas as pd
import numpy as np
import re
import joblib
from starlette.responses import StreamingResponse
import sklearn

app = FastAPI()


class Item(BaseModel):
    name: str
    year: int
    selling_price: int
    km_driven: int
    fuel: str
    seller_type: str
    transmission: str
    owner: str
    mileage: str
    engine: str
    max_power: str
    torque: str
    seats: float


class Items(BaseModel):
    objects: List[Item]


def delete_ed_izm(x):
    if pd.isnull(x):
        return x
    else:
        try:
            x = float(x.split()[0])
        except ValueError:
            x = np.NaN
        else:
            return x
        return x


def torque_change(x):
    if pd.isnull(x):
        return x

    x = x.lower()
    if '(' in x:
        tailed = x[x.index('(') + 1:].split('@')[0]
        x = x[:x.index('(')]
    if '/' in x:
        x = x.split('/')[0]
        tailed = 'nm'
    if '@' in x:
        x = x.split('@')[0]

    try:
        x = float(x)
    except ValueError:
        pass

    if type(x) == str:
        x = re.sub(r'\s+', '', x)

        match_nm = re.search(r'(\d+)([^\S\n\t]?)nm', x)
        match_kg = re.search(r'(\d+)([^\S\n\t]?)kgm', x)

        if match_kg:
            return float(match_kg.group(1)) * 9.80665
        elif match_nm:
            return float(match_nm.group(1))
        else:
            if tailed == 'kgm':
                return float(x) * 9.80665
            else:
                return float(x)
    else:
        return x


def max_torque(x):
    if pd.isnull(x):
        return x
    x = x.lower()
    if '@' in x:
        x = x.split('@')[1]
    if '(' in x:
        tailed = x[x.index('(') + 1:].split('@')[0]
        x = x[:x.index('(')]

    if '+/-' in x:
        x = re.sub(r'[a-zA-Z]', '', x.replace(',', '').strip())
        x = x.split("+/-")
        x = float(x[0]) + float(x[1])
    elif '/' in x:
        x = x.split('/')[1]

    if type(x) == str:
        x = re.sub(r'\s+', '', x)

        match_rpm = re.search(r'(\d+)([^\S\n\t]?)rpm', x)
        match_kg = re.search(r'(\d+)([^\S\n\t]?)kgm', x)

        if match_rpm:
            return float(match_rpm.group(1).replace(',', ''))
        else:
            if '-' in x:
                return float(x.split('-')[1].replace(',', ''))
            else:
                try:
                    x = float(x.replace(',', ''))
                except ValueError:
                    x = np.nan
                return x
    else:
        return x


def prepare_data(X, type='item'):
    dict_of_medians, scaler, encoder, _ = joblib.load(r'./ridge_model.pickle')

    X['max_torque_rpm'] = X['torque'].apply(max_torque)
    X['torque'] = X['torque'].apply(torque_change)
    for i in ['mileage', 'engine', 'max_power']:
        X[i] = X[i].apply(delete_ed_izm)

    for i in ['mileage', 'engine', 'max_power', 'torque', 'seats', 'max_torque_rpm']:
        X[i] = X[i].fillna(dict_of_medians[i])

    num_cols = [i for i in X.columns if
                i not in ['selling_price', 'name', 'fuel', 'seller_type', 'transmission', 'owner']]

    if type == 'items':
        X[num_cols] = scaler.transform(X[num_cols])

    X = X.drop(columns={'name', 'selling_price'})

    columns_to_encode = ['fuel', 'seller_type', 'transmission', 'owner', 'seats']
    test_encoded = encoder.transform(X[columns_to_encode])
    X = pd.concat(
        [X, pd.DataFrame(test_encoded, columns=encoder.get_feature_names_out(columns_to_encode))], axis=1)

    X = X.drop(columns=['fuel', 'seller_type', 'transmission', 'owner', 'seats'])
    X['year_squared'] = X['year'] ** 2
    X['km_driven_squared'] = X['km_driven'] ** 2
    X['torque_log'] = np.log(X['torque'])
    X['engine_log'] = np.log(X['engine'])

    return X


def predict(X):
    _, _, _, ridge = joblib.load(r'./ridge_model.pickle')
    return ridge.predict(X)


@app.post("/predict_item")
def predict_item(item: Item):
    item = pd.DataFrame(item.dict(), index=[0])
    item = prepare_data(item, 'item')
    pred = predict(item)[0]
    return JSONResponse(content={"predicted_cost": pred})


@app.post("/predict_items")
def predict_items(items: List[Item]):
    l = []
    for i in items:
        l.append(dict(i))
    df = pd.DataFrame.from_records(l)
    df_new = prepare_data(df)
    pred = predict(df_new)
    df['predicted_price'] = pred
    print(df)
    output_file = BytesIO()
    df.to_csv('./predicted_costs.csv', index=False)
    df.to_csv(output_file, index=False)
    output_file.seek(0)
    return StreamingResponse(content=output_file, media_type="application/octet-stream",
                             headers={'Content-Disposition': 'attachment; filename="predicted_costs.csv"'})
