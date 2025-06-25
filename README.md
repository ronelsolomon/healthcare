# Healthcare Plan Analysis and Chatbot

A Streamlit-based web application for analyzing healthcare plans and providing AI-powered assistance through a chatbot interface.

## Features

- **Interactive Dashboard**: Visualize and explore healthcare plan data
- **AI Chatbot**: Get answers to healthcare plan questions using a local language model
- **Data Management**: Store and manage healthcare plan information in a SQLite database
- **Data Export**: Export plan data to CSV format for further analysis

## Prerequisites

- Python 3.9+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd healthcare
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Dashboard
```bash
streamlit run dashboard.py
```

### Running the Chatbot
```bash
streamlit run chatbot.py
```

### Data Collection
To collect marketplace data:
```bash
python collect_marketplace_data.py
```

## Project Structure

- `app.py` - Main application file
- `chatbot.py` - AI chatbot implementation
- `dashboard.py` - Data visualization dashboard
- `db.py` - Database models and operations
- `collect_marketplace_data.py` - Script for collecting healthcare marketplace data
- `exported_csvs/` - Directory containing exported CSV files
- `models/` - Contains AI model files
- `marketplace.db` - SQLite database file

## Dependencies

- Streamlit - For building the web interface
- Pandas - For data manipulation
- Plotly - For data visualization
- LangChain - For AI model integration
- SQLAlchemy - For database operations
- python-dotenv - For environment variable management

## Configuration

Create a `.env` file in the root directory with the following variables:
```
# Database configuration
DATABASE_URL=sqlite:///marketplace.db

# AI model configuration (if applicable)
MODEL_PATH=./models/your-model.bin
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For support, please open an issue in the GitHub repository.
