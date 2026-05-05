from odoo import models

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
    

    def _pos_ui_models_to_load(self):
        res = super()._pos_ui_models_to_load()

        if 'stock.location' not in res:
            res.append('stock.location')

        return res

    # def _loader_params_stock_location(self):
    #     return {
    #         'search_params': {
    #             'domain': [('usage', '=', 'internal')],
    #             'fields': ['id', 'name', 'complete_name'],
    #         },
    #     }