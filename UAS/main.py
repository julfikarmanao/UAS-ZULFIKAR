from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import tb_printer as tb_printerModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'harga': 7, 'jumlah_pin': 4, 'resolusi': 3, 'tegangan_listrik': 4, 'berat': 2}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(tb_printerModel.printer, tb_printerModel.harga, tb_printerModel.jumlah_pin, tb_printerModel.resolusi, tb_printerModel.tegangan_listrik, tb_printerModel.berat)
        result = session.execute(query).fetchall()
        print(result)
        return [{'printer': tb_printer.printer, 'harga': tb_printer.harga, 'jumlah_pin': tb_printer.jumlah_pin, 'resolusi': tb_printer.resolusi, 'tegangan_listrik': tb_printer.tegangan_listrik, 'berat': tb_printer.berat} for tb_printer in result]

    @property
    def normalized_data(self):
        harga_values = []
        jumlah_pin_values = []
        resolusi_values = []
        tegangan_listrik_values = []
        berat_values = []

        for data in self.data:
            harga_values.append(data['harga'])
            jumlah_pin_values.append(data['jumlah_pin'])
            resolusi_values.append(data['resolusi'])
            tegangan_listrik_values.append(data['tegangan_listrik'])
            berat_values.append(data['berat'])

        return [
            {'printer': data['printer'],
             'harga': min(harga_values) / data['harga'],
             'jumlah_pin': data['jumlah_pin'] / max(jumlah_pin_values),
             'resolusi': data['resolusi'] / max(resolusi_values),
             'tegangan_listrik': data['tegangan_listrik'] / max(tegangan_listrik_values),
             'berat': data['berat'] / max(berat_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = []

        for row in normalized_data:
            product_score = (
                row['harga'] ** self.raw_weight['harga'] *
                row['jumlah_pin'] ** self.raw_weight['jumlah_pin'] *
                row['resolusi'] ** self.raw_weight['resolusi'] *
                row['tegangan_listrik'] ** self.raw_weight['tegangan_listrik'] *
                row['berat'] ** self.raw_weight['berat']
            )

            produk.append({
                'printer': row['printer'],
                'produk': product_score
            })

        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)

        sorted_data = []

        for product in sorted_produk:
            sorted_data.append({
                'printer': product['printer'],
                'score': product['produk']
            })

        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'data': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['printer']:
                  round(row['harga'] * weight['harga'] +
                        row['jumlah_pin'] * weight['jumlah_pin'] +
                        row['resolusi'] * weight['resolusi'] +
                        row['tegangan_listrik'] * weight['tegangan_listrik'] +
                        row['berat'] * weight['berat'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return result, HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'data': result}, HTTPStatus.OK.value


class tb_printer(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(tb_printerModel)
        data = [{'printer': tb_printer.printer, 'harga': tb_printer.harga, 'jumlah_pin': tb_printer.jumlah_pin, 'resolusi': tb_printer.resolusi, 'tegangan_listrik': tb_printer.tegangan_listrik, 'berat': tb_printer.berat} for tb_printer in session.scalars(query)]
        return self.get_paginated_result('tb_printer/', data, request.args), HTTPStatus.OK.value


api.add_resource(tb_printer, '/tb_printer')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)