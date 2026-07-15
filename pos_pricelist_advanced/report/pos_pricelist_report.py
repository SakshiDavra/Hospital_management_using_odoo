from odoo import fields, models, tools


class PosPricelistReport(models.Model):
    _name = "pos.pricelist.report"
    _description = "POS Pricelist Sales Report"
    _auto = False
    _rec_name = "pricelist_id"

    pricelist_id = fields.Many2one("product.pricelist", readonly=True)
    company_id = fields.Many2one("res.company", readonly=True)
    config_id = fields.Many2one("pos.config", readonly=True)
    session_id = fields.Many2one("pos.session", readonly=True)

    order_count = fields.Integer(readonly=True)
    qty = fields.Float(readonly=True)
    total = fields.Float(readonly=True)
    discount = fields.Float(readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (

                SELECT
                    MIN(pol.id) AS id,
                    po.pricelist_id AS pricelist_id,
                    po.company_id AS company_id,
                    po.config_id AS config_id,
                    po.session_id AS session_id,

                    COUNT(DISTINCT po.id) AS order_count,
                    SUM(pol.qty) AS qty,
                    SUM(pol.price_subtotal_incl) AS total,
                    SUM(pol.price_unit * pol.qty * pol.discount / 100.0) AS discount

                FROM pos_order_line pol
                JOIN pos_order po
                    ON po.id = pol.order_id

                WHERE po.pricelist_id IS NOT NULL

                GROUP BY
                    po.pricelist_id,
                    po.company_id,
                    po.config_id,
                    po.session_id
            )
        """)