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
			// Merge values by creating a new array to avoid mutating the caller's data.
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
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	const nodeRequire = require as any;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	const nodeModule = module as any;
	if (nodeRequire.main === nodeModule) {
		runMetricAnalyzerDemo();
	}
}
