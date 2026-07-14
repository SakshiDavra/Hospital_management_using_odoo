from odoo import models


class PosConfig(models.Model):
    _inherit = "pos.config"

    def write(self, vals):
        if "pos_available_pricelist_ids" in vals:
            for command in vals["pos_available_pricelist_ids"]:
                if command[0] == 4:
                    pricelist = self.env["product.pricelist"].browse(command[1])
                    if pricelist.state != "approved":
                        raise ValueError("Only approved pricelists can be selected.")
                elif command[0] == 6:
                    approved_ids = self.env["product.pricelist"].search([
                        ("id", "in", command[2]),
                        ("state", "=", "approved"), ]).ids
                    command[2][:] = approved_ids

        return super().write(vals)