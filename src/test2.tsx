/** @jsx h */

type Primitive = string | number | boolean | null | undefined;

type JSXChild = Primitive | JSXElement;

type JSXElement = {
	type: string;
	props: Record<string, unknown> & { children?: JSXChild[] };
};

declare const require: unknown;
declare const module: unknown;

declare global {
	namespace JSX {
		// eslint-disable-next-line @typescript-eslint/consistent-type-definitions
		interface IntrinsicElements {
			div: Record<string, unknown>;
			button: Record<string, unknown>;
			h1: Record<string, unknown>;
			p: Record<string, unknown>;
			ul: Record<string, unknown>;
			li: Record<string, unknown>;
			span: Record<string, unknown>;
			em: Record<string, unknown>;
		}
	}
}

function h(
	type: string,
	props: Record<string, unknown> | null,
	...children: JSXChild[]
): JSXElement {
	return {
		type,
		props: { ...(props ?? {}), children },
	};
}

type TodoItem = {
	id: number;
	title: string;
	completed: boolean;
};

const SAMPLE_TODOS: TodoItem[] = [
	{ id: 1, title: 'Write documentation', completed: true },
	{ id: 2, title: 'Ship new feature', completed: false },
	{ id: 3, title: 'Polish UI', completed: false },
];

export type TodoDashboardProps = {
	filterCompleted?: boolean | null;
};

export const TodoDashboard = ({
	filterCompleted = null,
}: TodoDashboardProps): JSXElement => {
	const todos = filterTodos(SAMPLE_TODOS, filterCompleted);
	const completedCount = SAMPLE_TODOS.filter((todo) => todo.completed).length;

	return (
		<div>
			<h1>Todo Dashboard Demo</h1>
			<p>Completed tasks: {completedCount}</p>
			{renderFilters(filterCompleted)}
			{todos.length === 0 ? renderEmptyState() : renderTodoList(todos)}
		</div>
	);
};

export const renderFilters = (filterCompleted: boolean | null): JSXElement => (
	<div>
		<button type='button' data-selected={filterCompleted === null}>
			Show all
		</button>
		<button type='button' data-selected={filterCompleted === true}>
			Show completed
		</button>
		<button type='button' data-selected={filterCompleted === false}>
			Show pending
		</button>
	</div>
);

export const renderEmptyState = (): JSXElement => <em>No todos to display.</em>;

export const renderTodoList = (todos: TodoItem[]): JSXElement => (
	<ul>
		{todos.map((todo) => (
			<li key={todo.id} data-completed={todo.completed}>
				<span>{todo.title}</span>
				<span>{todo.completed ? '✅' : '🕒'}</span>
			</li>
		))}
	</ul>
);

export const filterTodos = (
	todos: TodoItem[],
	filterCompleted: boolean | null
): TodoItem[] => {
	if (filterCompleted === null) {
		return todos;
	}

	return todos.filter((todo) => todo.completed === filterCompleted);
};

const indent = (depth: number): string => {
	if (depth <= 0) {
		return '';
	}

	let value = '';
	for (let index = 0; index < depth; index += 1) {
		value += '  ';
	}

	return value;
};

const trimRight = (value: string): string => value.replace(/[\s\n]+$/, '');

export const renderToString = (element: JSXChild, depth = 0): string => {
	if (element === null || element === undefined) {
		return '';
	}

	if (
		typeof element === 'string' ||
		typeof element === 'number' ||
		typeof element === 'boolean'
	) {
		return `${indent(depth)}${String(element)}\n`;
	}

	const { type, props } = element;
	const attrEntries: string[] = [];
	for (const key in props) {
		if (
			!Object.prototype.hasOwnProperty.call(props, key) ||
			key === 'children'
		) {
			continue;
		}

		const value = props[key];
		attrEntries.push(`${key}="${value}"`);
	}
	const attributes = attrEntries.length > 0 ? ` ${attrEntries.join(' ')}` : '';
	const children = props.children ?? [];

	const opening = `${indent(depth)}<${type}${attributes}>\n`;
	const childMarkup = children
		.map((child) => renderToString(child, depth + 1))
		.join('');
	const closing = `${indent(depth)}</${type}>\n`;

	return opening + childMarkup + closing;
};

export function runTodoDashboardDemo(): void {
	const views = [null, true, false].map((filter) => ({
		filter,
		markup: renderToString(<TodoDashboard filterCompleted={filter} />),
	}));

	for (const { filter, markup } of views) {
		const label = filter === null ? 'all' : filter ? 'completed' : 'pending';
		console.log(`\n--- rendering ${label} view ---`);
		console.log(trimRight(markup));
	}
}

// Avoid referencing Node globals when the script is bundled for the browser.
if (typeof require !== 'undefined' && typeof module !== 'undefined') {
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	const nodeRequire = require as any;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	const nodeModule = module as any;
	if (nodeRequire.main === nodeModule) {
		runTodoDashboardDemo();
	}
}
