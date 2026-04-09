/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class TodoList extends Component {

    setup() {
        this.orm = useService("orm");

        this.state = useState({
            todos: [],
            newTask: "",
            loading: false,
        });

        onMounted(() => {
            this.loadTodos();
        });
    }

    // ================= LOAD =================
    async loadTodos() {
        this.state.loading = true;

        const res = await this.orm.call(
            "hospital.todo",
            "get_todos",
            []
        );

        this.state.todos = res || [];
        this.state.loading = false;
    }

    // ================= ADD =================
    async addTodo() {
        if (!this.state.newTask.trim()) return;

        const newTodo = await this.orm.call(
            "hospital.todo",
            "add_todo",
            [this.state.newTask]
        );

        this.state.todos.push(newTodo);
        this.state.newTask = "";
    }

    // ================= TOGGLE =================
    async toggleTodo(todo) {
        await this.orm.call(
            "hospital.todo",
            "toggle_todo",
            [todo.id]
        );

        todo.is_done = !todo.is_done;
    }

    // ================= DELETE =================
    async deleteTodo(todo) {
        await this.orm.call(
            "hospital.todo",
            "delete_todo",
            [todo.id]
        );

        this.state.todos = this.state.todos.filter(t => t.id !== todo.id);
    }
}

TodoList.template = "hospital.TodoList";