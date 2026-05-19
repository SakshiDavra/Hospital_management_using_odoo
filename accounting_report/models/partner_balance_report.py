from odoo import fields, models, tools


class PartnerBalanceReport(models.Model):

    _name = 'partner.balance.report'
    _description = 'Partner Balance Report'
    _auto = False
    _rec_name = 'partner_id'

    company_currency_id = fields.Many2one(
        'res.currency',
        readonly=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        readonly=True
    )

    purchase_total = fields.Monetary(
        currency_field='company_currency_id',
        readonly=True
    )

    purchase_paid = fields.Monetary(
        currency_field='company_currency_id',
        readonly=True
    )

    purchase_due = fields.Monetary(
        currency_field='company_currency_id',
        readonly=True
    )

    sales_total = fields.Monetary(
        currency_field='company_currency_id',
        readonly=True
    )

    sales_received = fields.Monetary(
        currency_field='company_currency_id',
        readonly=True
    )

    sales_due = fields.Monetary(
        currency_field='company_currency_id',
        readonly=True
    )

    net_balance = fields.Monetary(
        currency_field='company_currency_id',
        readonly=True
    )

    status = fields.Selection([
        ('receivable', 'Receivable'),
        ('payable', 'Payable')
    ], readonly=True)

    def init(self):

        tools.drop_view_if_exists(
            self.env.cr,
            self._table
        )

        self.env.cr.execute("""

            CREATE OR REPLACE VIEW partner_balance_report AS (

                SELECT

                    ROW_NUMBER() OVER() AS id,

                    am.partner_id,

                    (
                        SELECT id
                        FROM res_currency
                        WHERE name = 'USD'
                        LIMIT 1
                    ) AS company_currency_id,

                    -- Purchase

                    SUM(
                        CASE
                            WHEN am.move_type = 'in_invoice'
                            THEN ABS(am.amount_total_signed)
                            ELSE 0
                        END
                    ) AS purchase_total,

                    SUM(
                        CASE
                            WHEN am.move_type = 'in_invoice'
                            THEN ABS(
                                am.amount_total_signed
                                - am.amount_residual_signed
                            )
                            ELSE 0
                        END
                    ) AS purchase_paid,

                    SUM(
                        CASE
                            WHEN am.move_type = 'in_invoice'
                            THEN ABS(am.amount_residual_signed)
                            ELSE 0
                        END
                    ) AS purchase_due,

                    -- Sales

                    SUM(
                        CASE
                            WHEN am.move_type = 'out_invoice'
                            THEN am.amount_total_signed
                            ELSE 0
                        END
                    ) AS sales_total,

                    SUM(
                        CASE
                            WHEN am.move_type = 'out_invoice'
                            THEN (
                                am.amount_total_signed
                                - am.amount_residual_signed
                            )
                            ELSE 0
                        END
                    ) AS sales_received,

                    SUM(
                        CASE
                            WHEN am.move_type = 'out_invoice'
                            THEN am.amount_residual_signed
                            ELSE 0
                        END
                    ) AS sales_due,

                    -- Net Balance

                    SUM(
                        CASE
                            WHEN am.move_type = 'out_invoice'
                            THEN am.amount_residual_signed
                            ELSE 0
                        END
                    )

                    -

                    SUM(
                        CASE
                            WHEN am.move_type = 'in_invoice'
                            THEN ABS(am.amount_residual_signed)
                            ELSE 0
                        END
                    ) AS net_balance,

                    CASE
                        WHEN

                            SUM(
                                CASE
                                    WHEN am.move_type = 'out_invoice'
                                    THEN am.amount_residual_signed
                                    ELSE 0
                                END
                            )

                            >

                            SUM(
                                CASE
                                    WHEN am.move_type = 'in_invoice'
                                    THEN ABS(am.amount_residual_signed)
                                    ELSE 0
                                END
                            )

                        THEN 'receivable'

                        ELSE 'payable'

                    END AS status

                FROM account_move am

                WHERE
                    am.state = 'posted'
                    AND am.partner_id IS NOT NULL
                    AND am.move_type IN (
                        'out_invoice',
                        'in_invoice'
                    )

                GROUP BY am.partner_id

            )

        """)

    def action_view_moves(self):

        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices & Bills',
            'res_model': 'account.move',
            'view_mode': 'list,form',

            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'posted'),
                ('move_type', 'in', [
                    'out_invoice',
                    'in_invoice'
                ])
            ],

            'context': {
                'create': False,
                'group_by': 'move_type',
                'expand': 1
            }
        }