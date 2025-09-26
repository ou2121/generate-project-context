# AI Context Report

- **Version**: `5.0.0`
- **Project Root**: `/Users/Documents/dev/others/project-context-generator`
- **Generated**: `2025-09-26 18:07:59`
- **Files discovered**: `3`

---

## `src/test1.js`

```js
class Calculator {
	add(a, b) {
		return a + b;
	}
	subtract(a, b) {
		return a - b;
	}
	multiply(a, b) {
		return a * b;
	}
	divide(a, b) {
		if (b === 0) {
			throw new Error('Cannot divide by zero');
		}
		return a / b;
	}
}
const calculator = new Calculator();
function assertAlmostEqual(actual, expected, message) {
	if (Math.abs(actual - expected) > 1e-9) {
		throw new Error(
			`Assertion failed: ${message}. Expected ${expected}, got ${actual}`
		);
	}
}
function runCalculatorDemo() {
	console.log('Running calculator demo...');
	const addResult = calculator.add(2, 3);
	console.log('2 + 3 =', addResult);
	assertAlmostEqual(addResult, 5, 'Addition should work');
	const subtractResult = calculator.subtract(10, 4);
	console.log('10 - 4 =', subtractResult);
	assertAlmostEqual(subtractResult, 6, 'Subtraction should work');
	const multiplyResult = calculator.multiply(6, 7);
	console.log('6 * 7 =', multiplyResult);
	assertAlmostEqual(multiplyResult, 42, 'Multiplication should work');
	const divideResult = calculator.divide(12, 3);
	console.log('12 / 3 =', divideResult);
	assertAlmostEqual(divideResult, 4, 'Division should work');
	try {
		calculator.divide(1, 0);
	} catch (error) {
		console.log('Expected error for divide by zero:', error.message);
	}
	console.log('All calculator checks passed!');
}
if (require.main === module) {
	runCalculatorDemo();
}
module.exports = {
	Calculator,
	runCalculatorDemo,
};
```

---

## `src/test2.tsx`

```tsx
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
if (typeof require !== 'undefined' && typeof module !== 'undefined') {
	const nodeRequire = require as any;
	const nodeModule = module as any;
	if (nodeRequire.main === nodeModule) {
		runTodoDashboardDemo();
	}
}
```

---

## `src/test3.ts`

```ts
type Metric = {
	name: string;
	values: number[];
};
type MetricSummary = {
	name: string;
	count: number;
	min: number;
	max: number;
	average: number;
	standardDeviation: number;
};
export class MetricAnalyzer {
	private readonly metrics: Metric[] = [];
	public addMetric(metric: Metric): void {
		let existingIndex = -1;
		for (let index = 0; index < this.metrics.length; index += 1) {
			if (this.metrics[index].name === metric.name) {
				existingIndex = index;
				break;
			}
		}
		if (existingIndex >= 0) {
			this.metrics[existingIndex] = {
				name: metric.name,
				values: this.metrics[existingIndex].values.concat(metric.values),
			};
		} else {
			this.metrics.push({
				name: metric.name,
				values: metric.values.slice(),
			});
		}
	}
	public summarize(): MetricSummary[] {
		return this.metrics.map((metric) => summarizeMetric(metric));
	}
	public clear(): void {
		this.metrics.length = 0;
	}
}
export const summarizeMetric = (metric: Metric): MetricSummary => {
	if (metric.values.length === 0) {
		return {
			name: metric.name,
			count: 0,
			min: 0,
			max: 0,
			average: 0,
			standardDeviation: 0,
		};
	}
	let sum = 0;
	let min = metric.values[0];
	let max = metric.values[0];
	for (let index = 0; index < metric.values.length; index += 1) {
		const value = metric.values[index];
		sum += value;
		if (value < min) {
			min = value;
		}
		if (value > max) {
			max = value;
		}
	}
	const count = metric.values.length;
	const average = sum / count;
	let squaredErrorSum = 0;
	for (let index = 0; index < count; index += 1) {
		const error = metric.values[index] - average;
		squaredErrorSum += error * error;
	}
	const variance = squaredErrorSum / count;
	const standardDeviation = Math.sqrt(variance);
	return {
		name: metric.name,
		count,
		min,
		max,
		average,
		standardDeviation,
	};
};
export const describeSummaries = (summaries: MetricSummary[]): string => {
	if (summaries.length === 0) {
		return 'No metrics recorded.';
	}
	const lines: string[] = [];
	for (let index = 0; index < summaries.length; index += 1) {
		const summary = summaries[index];
		lines.push(
			[
				`Metric: ${summary.name}`,
				`Count: ${summary.count}`,
				`Range: ${summary.min} - ${summary.max}`,
				`Average: ${summary.average.toFixed(2)}`,
				`Std Dev: ${summary.standardDeviation.toFixed(2)}`,
			].join(' | ')
		);
	}
	return lines.join('\n');
};
export const generateSampleMetrics = (): Metric[] => [
	{ name: 'response_time_ms', values: [120, 135, 150, 90, 105, 130] },
	{ name: 'memory_usage_mb', values: [256, 240, 232, 280, 300] },
	{ name: 'cpu_percent', values: [32, 44, 27, 55, 38, 41, 36] },
];
declare const require: unknown;
declare const module: unknown;
export function runMetricAnalyzerDemo(): void {
	const analyzer = new MetricAnalyzer();
	const metrics = generateSampleMetrics();
	for (let index = 0; index < metrics.length; index += 1) {
		analyzer.addMetric(metrics[index]);
	}
	const summaries = analyzer.summarize();
	const report = describeSummaries(summaries);
	console.log('Metric Analyzer Report');
	console.log('======================');
	console.log(report);
}
if (typeof require !== 'undefined' && typeof module !== 'undefined') {
	const nodeRequire = require as any;
	const nodeModule = module as any;
	if (nodeRequire.main === nodeModule) {
		runMetricAnalyzerDemo();
	}
}
```

---
