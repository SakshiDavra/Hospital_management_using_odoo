import logging
import re
from rapidfuzz import fuzz, process
from rapidfuzz.distance import Levenshtein
from odoo import api, models
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    STOP_WORDS = {
        "a", "an", "the", "is", "are", "am", "was", "were",
        "in", "on", "at", "to", "of", "for", "with", "and",
        "or", "from", "by", "into", "customer", "interested",
        "interest", "want", "wants", "wanted", "looking",
        "needs", "need", "new",
    }

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._apply_assignment_rule()
        return leads

    def _get_score_skill(self, rule_type, score):
        if not rule_type or not rule_type.score_line_ids:
            return False
        line = rule_type.score_line_ids.filtered(lambda l: l.from_score <= score <= l.to_score)
        return line.skill_id.name if line else False

    def _extract_description_matches(self, model_name, description):
        if not description or not model_name or model_name not in self.env:
            return []
            
        clean_desc = re.sub(r"[^\w\s]", " ", html2plaintext(description).lower())
        try:
            from spellchecker import SpellChecker
            spell = SpellChecker()
            tokens = [spell.correction(w) or w if len(w) > 2 and w not in self.STOP_WORDS else w for w in clean_desc.split()]
            clean_desc = " ".join(tokens)
        except Exception as e:
            _logger.warning("Spell checker skipped: %s", e)

        tokens = {w for w in re.findall(r"\b\w+\b", clean_desc) if len(w) > 2 and w not in self.STOP_WORDS}
        if not tokens:
            return []

        candidates = self.env[model_name].search([])
        if not candidates:
            return []

        min_score = 85 if "product" in model_name else 90
        max_distance = 2 if "product" in model_name else 1
        required_ratio = 0.7
        scored_candidates = []

        for rec in candidates:
            if not rec.name:
                continue
            rec_tokens = {w for w in re.findall(r"\b\w+\b", rec.name.lower()) if len(w) > 2 and w not in self.STOP_WORDS}
            if not rec_tokens:
                continue

            total_score, matched_count, used_tokens = 0, 0, set()
            for ptoken in rec_tokens:
                best = process.extractOne(ptoken, tokens, scorer=fuzz.ratio)
                if not best:
                    continue
                matched_token, score, _ = best
                if matched_token in used_tokens:
                    continue

                if score >= min_score and Levenshtein.distance(ptoken, matched_token) <= max_distance:
                    used_tokens.add(matched_token)
                    total_score += score
                    matched_count += 1  # Fixed SyntaxError here

            matched_ratio = matched_count / len(rec_tokens) if rec_tokens else 0.0
            if matched_ratio >= required_ratio:
                scored_candidates.append({
                    'name': rec.name,
                    'matched_ratio': matched_ratio,
                    'total_match_score': total_score,
                    'overall_score': fuzz.token_set_ratio(rec.name.lower(), clean_desc)
                })

        if not scored_candidates:
            return []

        scored_candidates.sort(key=lambda x: (x['matched_ratio'], x['total_match_score'], x['overall_score']), reverse=True)
        return [scored_candidates[0]['name']]

    def _process_rule_filtering(self, rule, lead, employees):
        rule_type = rule.rule_type_id
        processing = rule_type.processing_type
        field_name = rule_type.lead_field_id.name if rule_type.lead_field_id else False

        if processing == "existing_customer":
            if lead.partner_id and lead.partner_id.user_id:
                lead.user_id = lead.partner_id.user_id
                return rule, employees, True
            return rule, employees, False

        if processing == "round_robin":
            return rule, employees, False

        if not field_name and processing != "description":
            return rule, employees, False

        if processing == "score":
            skill = self._get_score_skill(rule_type, lead[field_name])
            values = [skill] if skill else []
        elif processing == "description":
            # Fixed recordset field check using ._fields
            lead_val = lead[field_name] if field_name and field_name in lead._fields else ""
            values = self._extract_description_matches(rule_type.match_model_id.model, lead_val)
        else:
            field_value = lead[field_name] if field_name and field_name in lead._fields else False
            values = field_value.mapped("name") if isinstance(field_value, models.BaseModel) else [field_value]

        normalized = {str(v).strip().lower() for v in values if v or v == 0}
        if not normalized:
            return rule, self.env["hr.employee"], False

        filtered_emps = employees.filtered(
            lambda emp: rule_type.skill_type_id and bool(normalized.intersection({(s.skill_id.name or "").strip().lower() for s in emp.employee_skill_ids.filtered(lambda s: s.skill_type_id == rule_type.skill_type_id)}))
        )
        return rule, filtered_emps, False

    def _apply_assignment_rule(self):
        for lead in self:
            rules = self.env["crm.assignment.rule"].search([("active", "=", True), ("company_id", "=", lead.company_id.id)], order="sequence, id")
            if not rules:
                lead.user_id = False
                continue

            employees = self.env["hr.employee"].search([("user_id", "!=", False), ("company_id", "=", lead.company_id.id)])
            if not employees:
                lead.user_id = False
                continue

            matched_rule, assigned = None, False
            for rule in rules:
                if rule.rule_type_id.processing_type == "round_robin":
                    matched_rule = rule
                    break
                matched_rule, employees, assigned = self._process_rule_filtering(rule, lead, employees)
                if assigned or not employees:
                    break

            if assigned:
                continue

            if matched_rule and employees:
                lead._assign_user(matched_rule, employees)
            else:
                lead.user_id = False

    def _assign_user(self, rule, employees):
        self.ensure_one()
        users = employees.mapped("user_id")
        if not users:
            return
        
        user_lead_counts = {
            u.id: self.env['crm.lead'].search_count([('user_id', '=', u.id), ('stage_id.fold', '=', False)])
            for u in users
        }
        selected_user = min(users, key=lambda u: (user_lead_counts.get(u.id, 0), u.id))
        self.user_id = selected_user