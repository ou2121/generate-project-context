
/**
 * Dummy script that exercises a handful of utility functions.
 * Run with `node src/test1.js` to see the sample output.
 */

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
        throw new Error(`Assertion failed: ${message}. Expected ${expected}, got ${actual}`);
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
