from odoo import models,api


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_config(self):
        res = super()._loader_params_pos_config()

        fields = res['search_params'].get('fields', [])

        if 'currency_id' not in fields:
            fields.append('currency_id')

        custom_fields = [
            'enable_card_resize',
            'product_card_width',
            'product_card_height',
            'product_font_size'
        ]

        for f in custom_fields:
            if f not in fields:
                fields.append(f)

        res['search_params']['fields'] = fields

        return res

    def _loader_params_pos_config(self):
        res = super()._loader_params_pos_config()
        # પ્રોપર રીતે ફિલ્ડ્સ ચેક કરીને ઉમેરવા
        custom_fields = [
            'enable_card_resize',
            'product_card_width',
            'product_card_height',
            'product_font_size'
        ]
        
        # ખાતરી કરવી કે search_params અને fields અસ્તિત્વમાં છે
        if 'search_params' in res:
            fields = res['search_params'].get('fields', [])
            for f in custom_fields:
                if f not in fields:
                    fields.append(f)
            res['search_params']['fields'] = fields
        
        return res

    @api.model
    def _load_pos_data_models(self, config):
        data = super()._load_pos_data_models(config)
        # Production level માં મોડલ્સ ઉમેરવાની સાચી રીત
        models_to_add = ['stock.location', 'stock.quant']
        for model in models_to_add:
            if model not in data:
                data.append(model)
        return data
    

    