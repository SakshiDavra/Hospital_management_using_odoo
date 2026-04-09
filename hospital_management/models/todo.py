from odoo import models, fields, api

class HospitalTodo(models.Model):
    _name = 'hospital.todo'
    _description = 'Hospital Todo'

    name = fields.Char(string="Task", required=True)
    is_done = fields.Boolean(string="Done")

    from odoo import models, fields

class HospitalTodo(models.Model):
    _name = 'hospital.todo'
    _description = 'Hospital Todo'

    name = fields.Char(string="Task", required=True)
    is_done = fields.Boolean(string="Done")

    # GET TODOS
    @api.model
    def get_todos(self):
        todos = self.search([])
        return [{
            "id": t.id,
            "name": t.name,
            "is_done": t.is_done
        } for t in todos]

    # ADD TODO
    @api.model
    def add_todo(self, name):
        todo = self.create({
            "name": name,
            "is_done": False
        })
        return {
            "id": todo.id,
            "name": todo.name,
            "is_done": todo.is_done
        }

    # TOGGLE DONE
    @api.model
    def toggle_todo(self, todo_id):
        todo = self.browse(todo_id)
        todo.is_done = not todo.is_done
        return True

    # DELETE TODO
    @api.model
    def delete_todo(self, todo_id):
        self.browse(todo_id).unlink()
        return True