// --- Simple Calculator Module ---
const Calculator = {
  add(a, b) {
    return a + b;
  },
  subtract(a, b) {
    return a - b;
  },
  multiply(a, b) {
    return a * b;
  },
  divide(a, b) {
    if (b === 0) return "Error: Division by zero";
    return a / b;
  }
};

// Example usage:
console.log("Add:", Calculator.add(10, 5));
console.log("Subtract:", Calculator.subtract(10, 5));
console.log("Multiply:", Calculator.multiply(10, 5));
console.log("Divide:", Calculator.divide(10, 5));

// --- Dummy Weather Data ---
const weatherData = {
  "new york": {
    temperature: 12,
    condition: "Cloudy",
    humidity: 60,
    wind: 10
  },
  "los angeles": {
    temperature: 28,
    condition: "Sunny",
    humidity: 35,
    wind: 5
  },
  "london": {
    temperature: 9,
    condition: "Rainy",
    humidity: 80,
    wind: 12
  },
  "tokyo": {
    temperature: 18,
    condition: "Partly Cloudy",
    humidity: 55,
    wind: 8
  }
};

// --- Weather Reply Function ---
function getWeatherReply(city) {
  const key = city.toLowerCase();
  const data = weatherData[key];

  if (!data) {
    return `Sorry, I don't have weather data for "${city}".`;
  }

  return (
    `Weather in ${city}:\n` +
    `• Temperature: ${data.temperature}°C\n` +
    `• Condition: ${data.condition}\n` +
    `• Humidity: ${data.humidity}%\n` +
    `• Wind: ${data.wind} km/h\n`
  );
}

// Example usage:
console.log(getWeatherReply("Tokyo"));
console.log(getWeatherReply("New York"));
console.log(getWeatherReply("Unknown City"));
const App = {
  Calculator,
  weatherData,
  getWeatherReply
};

console.log(App.Calculator.multiply(6, 7));
console.log(App.getWeatherReply("London"));
