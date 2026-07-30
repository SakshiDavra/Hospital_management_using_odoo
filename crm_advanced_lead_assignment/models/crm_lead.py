import re
from rapidfuzz import fuzz, process
from odoo import api, models
from odoo.tools import html2plaintext
import logging

_logger = logging.getLogger(__name__)

try:
    from spellchecker import SpellChecker
    _SPELL = SpellChecker()
except Exception:
    _SPELL = None


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

    def _tokenize(self, text):
        if not text:
            return set()
        return {
            w for w in re.findall(r"\b\w+\b", text)
            if w not in self.STOP_WORDS
        }

    def _get_score_skill(self, rule_type, score):
        if not rule_type or not rule_type.score_line_ids:
            return False
        line = rule_type.score_line_ids.filtered(lambda l: l.from_score <= score <= l.to_score)
        return line.skill_id.name if line else False

    def _extract_description_matches(self, model_name, description):
        if not description or not model_name or model_name not in self.env:
            return []
        raw_desc = html2plaintext(description)
        clean_desc = re.sub(r"[^\w\s]", " ", raw_desc.lower())
        if _SPELL:
            try:
                tokens_list = []
                for w in clean_desc.split():
                    if len(w) > 2 and w not in self.STOP_WORDS:
                        corrected = _SPELL.correction(w) or w
                        tokens_list.append(corrected)
                    else:
                        tokens_list.append(w)
                clean_desc = " ".join(tokens_list)
            except Exception:
                pass
        tokens = self._tokenize(clean_desc)
        if not tokens:
            return []

        domain = ['|'] * (len(tokens) - 1)
        for token in tokens:
            domain.append(('name', 'ilike', token))
        candidate_records = self.env[model_name].search(domain)
        
        if not candidate_records:
            return []

        min_score = 85 if "product" in model_name else 90
        required_ratio = 0.7
        scored_candidates = []
        for rec in candidate_records:
            rec_name = rec.name or ""
            rec_name_lower = rec_name.lower()

            rec_tokens = self._tokenize(rec_name_lower)
            if not rec_tokens:
                continue

            total_score, matched_count, used_tokens = 0, 0, set()
            for ptoken in rec_tokens:
                best = process.extractOne(ptoken, tokens, scorer=fuzz.ratio)
                if not best:
                    continue
                matched_token, score, _ = best

                if matched_token not in used_tokens and score >= min_score:
                    used_tokens.add(matched_token)
                    total_score += score
                    matched_count += 1

            matched_ratio = matched_count / len(rec_tokens)
            if matched_ratio >= required_ratio:
                overall_score = fuzz.token_set_ratio(rec_name_lower, clean_desc)                
                scored_candidates.append({
                    'name': rec_name,
                    'matched_ratio': matched_ratio,
                    'total_match_score': total_score,
                    'overall_score': overall_score
                })

        if not scored_candidates:
            return []
        best = max(scored_candidates,
            key=lambda x: (x['matched_ratio'],x['total_match_score'],x['overall_score']))
        return [best['name']]

    def _emp_matches(self, employee, rule_type, normalized):
        skills = employee.employee_skill_ids.filtered(lambda s: s.skill_type_id == rule_type.skill_type_id)
        emp_skills = { (s.skill_id.name or "").strip().lower()
            for s in skills}
        return bool(normalized.intersection(emp_skills))

    def _get_rule_values(self, rule_type, lead):
        processing = rule_type.processing_type
        field_name = rule_type.lead_field_id.name
        if processing == "score":
            skill = self._get_score_skill(rule_type, lead[field_name])
            return [skill] if skill else []
        elif processing == "description":
            return self._extract_description_matches(rule_type.match_model_id.model, lead[field_name] or "",)
        field_value = lead[field_name]
        return (field_value.mapped("name")
            if isinstance(field_value, models.BaseModel)
            else [field_value]
        )
    
    def _process_rule_filtering(self, rule, lead, employees):
        rule_type = rule.rule_type_id
        processing = rule_type.processing_type
        if processing == "existing_customer":
            if lead.partner_id.user_id:
                lead.user_id = lead.partner_id.user_id
                return rule, employees, True
            return rule, employees, False
        
        elif processing == "round_robin":
            return rule, employees, False
        
        values = self._get_rule_values(rule_type, lead)
        normalized = {str(v).strip().lower() for v in values if v or v == 0}
        if not normalized:
            return rule, self.env["hr.employee"], False
        filtered = employees.filtered(lambda emp: self._emp_matches(emp, rule_type, normalized))
        return rule, filtered, False

    def _apply_assignment_rule(self):
        for lead in self:
            rules = self.env["crm.assignment.rule"].search([("active", "=", True), ("company_id", "=", lead.company_id.id)], order="sequence, id")
            employees = self.env["hr.employee"].search([("user_id", "!=", False), ("company_id", "=", lead.company_id.id)])
            if not rules or not employees:
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
                lead._assign_user(employees)
            else:
                lead.user_id = False

    def _assign_user(self, employees):
        self.ensure_one()
        users = employees.mapped("user_id")
        if not users:
            return
        user_lead_counts = {}
        for u in users:
            count = self.env["crm.lead"].search_count([
                ("user_id", "=", u.id),("stage_id.name", "!=", "Won"),
            ])
            user_lead_counts[u.id] = count    
        selected_user = min(users,key=lambda u: (user_lead_counts.get(u.id, 0), u.id))
        self.user_id = selected_user