// Fetch Monthly/Seasonal Demand data and render chart
function fetchDemandTrend() {
    fetch('/api/demand-trend')
    .then(response => response.json())
    .then(data => {
        var demandTrendChart = JSON.parse(data);
        Plotly.newPlot('demandTrendChart', demandTrendChart.data, demandTrendChart.layout);
    })
    .catch(error => console.error('Error fetching demand trend data:', error));
}

// Fetch Product Categories Purchased data and render chart
function fetchProductCategories() {
    fetch('/api/product-categories')
    .then(response => response.json())
    .then(data => {
        var productCategoryChart = JSON.parse(data);
        Plotly.newPlot('productCategoryChart', productCategoryChart.data, productCategoryChart.layout);
    })
    .catch(error => console.error('Error fetching product categories data:', error));
}

// Fetch Customer Complaints data and render chart
function fetchCustomerComplaints() {
    fetch('/api/customer-complaints')
    .then(response => response.json())
    .then(data => {
        var complaintsWordCloud = JSON.parse(data);
        Plotly.newPlot('complaintsWordCloud', complaintsWordCloud.data, complaintsWordCloud.layout);
    })
    .catch(error => console.error('Error fetching customer complaints data:', error));
}

// Fetch Feedback Trends data and render chart
function fetchFeedbackTrends() {
    fetch('/api/feedback-trends')
    .then(response => response.json())
    .then(data => {
        var feedbackTrendsChart = JSON.parse(data);
        Plotly.newPlot('feedbackTrendsChart', feedbackTrendsChart.data, feedbackTrendsChart.layout);
    })
    .catch(error => console.error('Error fetching feedback trends data:', error));
}

// Fetch Top Selling Products data and render chart
function fetchTopSellingProducts() {
    fetch('/api/top-selling-products')
    .then(response => response.json())
    .then(data => {
        var topSellingProductsChart = JSON.parse(data);
        Plotly.newPlot('topSellingProductsChart', topSellingProductsChart.data, topSellingProductsChart.layout);
    })
    .catch(error => console.error('Error fetching top selling products data:', error));
}

// Fetch Product Sales by Region data and render chart
function fetchSalesByRegion() {
    fetch('/api/sales-by-region')
    .then(response => response.json())
    .then(data => {
        var salesByRegionChart = JSON.parse(data);
        Plotly.newPlot('salesByRegionChart', salesByRegionChart.data, salesByRegionChart.layout);
    })
    .catch(error => console.error('Error fetching sales by region data:', error));
}

// Fetch Product Return Rate data and render chart
function fetchReturnRate() {
    fetch('/api/return-rate')
    .then(response => response.json())
    .then(data => {
        var returnRateChart = JSON.parse(data);
        Plotly.newPlot('returnRateChart', returnRateChart.data, returnRateChart.layout);
    })
    .catch(error => console.error('Error fetching return rate data:', error));
}

// Load all the charts when the page loads
window.onload = function() {
    fetchDemandTrend();
    fetchProductCategories();
    fetchCustomerComplaints();
    fetchFeedbackTrends();
    fetchTopSellingProducts();
    fetchSalesByRegion();
    fetchReturnRate();
};