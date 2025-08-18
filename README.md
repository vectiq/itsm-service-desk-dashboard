# 🎫 ITSM Service Desk Dashboard

A comprehensive ITSM (IT Service Management) dashboard built with Streamlit that provides powerful visualizations and analytics for incident management, knowledge base administration, and service performance monitoring.

## ✨ Features

### 🎫 Incidents Dashboard
- **Complete Incident Management**: View, filter, and analyze all resolved incidents
- **Advanced Filtering**: Filter by priority, category, service, and location
- **Comprehensive Analytics**: Priority distribution, resolution time analysis, channel breakdown
- **Current Queue Management**: Real-time workload tracking with SLA monitoring

### 📚 Knowledge Base
- **Article Management**: Browse and search knowledge base articles
- **Template Library**: Access and manage KB templates
- **Coverage Analysis**: Identify knowledge gaps and coverage metrics
- **Category-based Organization**: Hierarchical knowledge organization

### 📊 Service Analytics
- **Service Performance**: Monitor service health and incident patterns
- **Trend Analysis**: Daily and weekly incident trends with pattern recognition
- **SLA Monitoring**: Priority matrix analysis and resolution time statistics
- **Category Hierarchy**: Visual representation of incident categorization

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/vectiq/itsm-service-desk-dashboard.git
   cd itsm-service-desk-dashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare your data**
   - Place your CSV files in a directory
   - Update the `HARDCODED_DATA_DIR` path in `app.py` to point to your data directory

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the dashboard**
   - Open your browser to `http://localhost:8501`

## 📁 Data Structure

The application expects the following CSV files:

### Core Files
- **`incidents_resolved.csv`**: Historical incident data with resolutions
- **`workload_queue.csv`**: Current open incidents/requests
- **`kb_articles.csv`**: Knowledge base articles
- **`kb_templates.csv`**: Knowledge base templates
- **`services_catalog.csv`**: Service catalog and definitions
- **`category_tree.csv`**: Incident category hierarchy

### Supporting Files
- **`priority_matrix.csv`**: Priority calculation matrix
- **`users_agents.csv`**: User and agent information
- **Additional CSV files**: The application automatically loads all CSV files in the data directory

## 🛠️ Configuration

### Data Directory
Update the data directory path in `app.py`:

```python
HARDCODED_DATA_DIR = "/path/to/your/csv/files"
```

### Customization
- **Styling**: Modify the Streamlit theme in `.streamlit/config.toml`
- **Metrics**: Customize KPI calculations in individual page files
- **Visualizations**: Adjust Plotly chart configurations for your needs

## 📊 Key Metrics Tracked

- **Incident Volume**: Total resolved incidents and current queue size
- **Priority Distribution**: P1, P2, P3, P4 incident breakdown
- **Resolution Performance**: Average resolution times by priority and service
- **Channel Analysis**: Incident sources (Email, Portal, Phone, Chat)
- **Service Impact**: Most affected services and categories
- **Knowledge Coverage**: KB article coverage vs incident categories
- **SLA Compliance**: Due dates and overdue tracking

## 🎨 Technology Stack

- **Frontend**: Streamlit
- **Visualizations**: Plotly Express & Graph Objects
- **Data Processing**: Pandas, NumPy
- **Styling**: Custom CSS with Streamlit theming
- **Python**: 3.8+

## 📱 Pages Overview

### 🏠 Home Dashboard
- Key metrics overview
- Data loading status
- Quick data preview

### 🎫 Incidents Dashboard
- All incidents with advanced filtering
- Priority and resolution analytics
- Current queue management

### 📚 Knowledge Base
- Article browsing and search
- Template management
- Coverage gap analysis

### 📊 Service Analytics
- Service performance monitoring
- Trend analysis and patterns
- SLA and priority analysis

## 🔧 Development

### Project Structure
```
itsm-service-desk-dashboard/
├── app.py                          # Main application entry point
├── pages/
│   ├── 1_🎫_Incidents_Dashboard.py # Incidents management
│   ├── 2_📚_Knowledge_Base.py      # KB management
│   └── 3_📊_Service_Analytics.py   # Service analytics
├── requirements.txt                # Python dependencies
├── .gitignore                     # Git ignore patterns
└── README.md                      # This file
```

### Adding New Features
1. Create new page files in the `pages/` directory
2. Follow the existing naming convention: `N_🔸_Page_Name.py`
3. Use consistent styling and layout patterns
4. Add appropriate error handling and data validation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Visualizations powered by [Plotly](https://plotly.com/)
- Data processing with [Pandas](https://pandas.pydata.org/)

---

**Made with ❤️ for ITSM professionals**
