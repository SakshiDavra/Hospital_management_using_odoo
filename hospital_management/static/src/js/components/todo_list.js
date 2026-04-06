/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

export class TodoList extends Component {

    static template = "hospital_todo_list_template";
    setup() {
        this.state = useState({
            filter: "all",
        });
    }
    // FILTER LOGIC
    get filteredTodos() {
        if (this.state.filter === "done") {
            return this.props.todos.filter(t => t.is_done);
        }
        if (this.state.filter === "pending") {
            return this.props.todos.filter(t => !t.is_done);
        }
        return this.props.todos;
    }

    // COUNTER LOGIC
    get total() {
        return this.props.todos.length;
    }

    get doneCount() {
        return this.props.todos.filter(t => t.is_done).length;
    }

    get pendingCount() {
        return this.total - this.doneCount;
    }
    async toggleTodo(todo) {
        await rpc("/hospital/todo/toggle", { id: todo.id });

        // UI update
        todo.is_done = !todo.is_done;
    }

    async deleteTodo(todo) {
        await rpc("/hospital/todo/delete", { id: todo.id });

        // remove from list
        this.props.todos.splice(this.props.todos.indexOf(todo), 1);
    }

    async addTodo() {

        const input = document.querySelector(".todo-input");

        const name = input.value.trim();
        if (!name) return;

        const res = await rpc("/hospital/todo/create", { name });
        // new data on top
        this.props.todos.unshift(res);

        input.value = "";
    }
}