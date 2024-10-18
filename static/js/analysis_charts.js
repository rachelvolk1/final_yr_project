// Line Chart: Fraud Trends Over Time
var fraudTrendData = {
    labels: ["January", "February", "March", "April", "May", "June"],
    datasets: [{
      label: 'Fraudulent Transactions Detected',
      data: [5, 9, 12, 8, 15, 7], // Ensure this is populated with actual data
      borderColor: "rgba(75, 192, 192, 1)",
      backgroundColor: "rgba(75, 192, 192, 0.2)",
      fill: true
    }]
  };
  
  var ctx = document.getElementById('fraudTrendLineChart').getContext('2d');
  var fraudTrendLineChart = new Chart(ctx, {
    // Line chart configuration
    type: 'line',
    data: fraudTrendData,
    options: {
      responsive: true,
      title: {
        display: true,
        text: 'Fraud Trends Over Time'
      },
      scales: {
        xAxes: [{ display: true }],
        yAxes: [{ display: true }]
      }
    }
  });
  
  // Donut Chart: Fraud by Payment Method
  var fraudByMethodData = {
    labels: ["Mobile Money", "Credit Card", "Bank Transfer", "Cash"], // Example data
    datasets: [{
      data: [40, 30, 20, 10], // Example data
      backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"],
      hoverBackgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
    }]
  };
  
  var ctx = document.getElementById('fraudByMethodDonutChart').getContext('2d');
var fraudByMethodDonutChart = new Chart(ctx, {
  // Donut chart configuration
    type: 'doughnut',
    data: fraudByMethodData,
    options: {
      responsive: true,
      title: {
        display: true,
        text: 'Fraud by Payment Method'
      }
    }
  });
  