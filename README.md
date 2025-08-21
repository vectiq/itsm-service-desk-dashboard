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

3. **Set up MongoDB**
   - Install and start MongoDB locally or use MongoDB Atlas
   - The application will connect to MongoDB automatically
   - Generate sample data using the AI-powered data generation feature

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the dashboard**
   - Open your browser to `http://localhost:8501`

## 📁 Data Structure

The application uses MongoDB collections for data storage:

### Core Collections
- **`incidents`**: All incident data (resolved and unresolved)
- **`agents`**: Agent information and skills
- **`kb_articles`**: Knowledge base articles
- **`settings`**: Application configuration and AI model settings

### AI-Generated Data
- **Incident Generation**: Create realistic incidents using AWS Bedrock
- **Agent Data**: Generate agent profiles with skills and capacity
- **Knowledge Articles**: AI-generated KB articles from incident patterns

## 🛠️ Configuration

### Data Storage
The application uses MongoDB for data storage:

- **MongoDB**: Primary database for all ITSM data
- **AI Generation**: Use AWS Bedrock to generate realistic incident data
- **Data Management**: Access the Data Management page to generate and manage data

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
